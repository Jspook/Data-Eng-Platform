# Architecture Decision Records (ADR)
## E-commerce End-to-End Data Platform

เอกสารฉบับนี้บันทึกเหตุผลเบื้องหลังการตัดสินใจเชิงวิศวกรรม (Engineering Decisions) พร้อมทั้งการวิเคราะห์ข้อดี ข้อเสีย และสิ่งที่ต้องแลกเปลี่ยน (Trade-offs) ตามมาตรฐานการออกแบบระบบระดับ Production

---

### ADR 001: Data Architecture Pattern — Medallion Architecture (Bronze / Silver / Gold)

- **บริบท (Context):** แพลตฟอร์มต้องการรองรับข้อมูลธุรกรรมอีคอมเมิร์ซ (Customers, Orders, Items, Payments) ที่มีทั้งข้อมูลดิบ ข้อมูลที่ต้องชำระล้าง และตารางรายงานผลลัพธ์
- **การตัดสินใจ (Decision):** ใช้ Medallion Architecture แบ่งข้อมูลเป็น 3 เลเยอร์:
  1. **Bronze (Raw Lake / Staging):** จัดเก็บข้อมูลดิบตามสภาพต้นทาง 100% ไม่แตะต้องตรรกะทางธุรกิจ
  2. **Silver (Cleaned & Conformed):** ทำ Data Cleansing, Deduplication, Type Casting, และ Standardization
  3. **Gold (Curated Star Schema):** ตารางมิติ (Dimensions) และตารางข้อเท็จจริง (Facts) พร้อมใช้งานสำหรับ Business Intelligence
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:* ความสามารถในการ Re-process ข้อมูลย้อนหลังได้เสมอหากตรรกะทางธุรกิจเปลี่ยน, มี Data Quality Gate ที่ชัดเจนระหว่างเลเยอร์, Lineage ชัดเจน
  - *ข้อเสีย:* ใช้พื้นที่จัดเก็บ (Storage footprint) เพิ่มขึ้นเนื่องจากเก็บข้อมูลซ้ำ 3 ระดับ และมี Latency เพิ่มขึ้นจากการ Transform หลายทอด

---

### ADR 002: Storage & Data Warehouse — PostgreSQL on Docker (Local) to Cloud-Ready DW

- **บริบท (Context):** ต้องการ Data Warehouse สำหรับการประมวลผล Local Development ที่ไม่ต้องเสียค่าใช้จ่าย Cloud แต่สถาปัตยกรรมต้องพร้อม Lift-and-Shift สู่ Cloud Data Warehouse (เช่น BigQuery / Snowflake)
- **การตัดสินใจ (Decision):** ใช้ **PostgreSQL 16** โดยแยก Schema ภายในฐานข้อมูลเดียวกัน (`bronze`, `silver`, `gold`)
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:* เป็น Open-Source, มาตรฐาน SQL สากล, รองรับ dbt-postgres อย่างสมบูรณ์, ใช้งานทรัพยากรเครื่องน้อย รันบน Docker ง่าย
  - *ข้อเสีย:* เป็น Row-oriented RDBMS ไม่ใช่ Massively Parallel Processing (MPP) Columnar Warehouse (เช่น BigQuery/ClickHouse) จึงไม่เหมาะกับระดับ Big Data ระดับหลาย Terabytes แต่สามารถพอร์ต Model บน dbt ไปยัง Cloud DW ได้ง่ายในภายหลังโดยแทบไม่ต้องแก้ SQL logic

---

### ADR 003: Object Storage / Data Lake — MinIO (S3 Compatible)

- **บริบท (Context):** ต้องการ Landing Zone / Data Lake จำลองสำหรับ Raw Ingestion File ก่อนนำเข้าสู่ Database
- **การตัดสินใจ (Decision):** ใช้ **MinIO** ในฐานะ S3-compatible Object Storage
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:* มี Web Console สำหรับตรวจสอบไฟล์ดิบ, รองรับ S3 API และ AWS SDK (`boto3`, MinIO Client), โค้ด Ingestion ที่เขียนสามารถสลับไปชี้ AWS S3 จริงได้ทันทีเพียงเปลี่ยน Endpoint URL
  - *ข้อเสีย:* เพิ่ม Container Service อีก 1 ตัวใน Docker Compose ซึ่งต้องดูแลเครือข่ายและการ Mount Persistent Volumes

---

### ADR 004: Data Transformation — dbt (data build tool)

- **บริบท (Context):** เดิมทีวิศวกรข้อมูลมักเขียนสคริปต์ Python หรือ Stored Procedure ในการแปลงข้อมูล ซึ่งยากต่อการ Version Control, ตรวจสอบ Lineage, และทำ Automated Testing
- **การตัดสินใจ (Decision):** ใช้ **dbt** เป็นเครื่องมือหลักในการทำ Transformation ภายใน Data Warehouse
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:*
    - เปลี่ยน Transformation ให้กลายเป็น Code (Software Engineering Best Practices)
    - รองรับการทำ Data Testing ในตัว (unique, not_null, accepted_values, relationships)
    - มี Documentation & DAG Lineage อัตโนมัติ
    - จัดการ Modular Model (staging → intermediate → marts) ได้อย่างเป็นระบบ
  - *ข้อเสีย:* ต้องใช้ SQL เป็นหลัก หากมีการคำนวณขั้นสูงที่ต้องการ Machine Learning หรือ Complex Graph Processing อาจต้องใช้ Python/PySpark เสริม

---

### ADR 005: Data Modeling — Kimball Dimensional Modeling (Star Schema)

- **บริบท (Context):** ผู้บริหารและนักวิเคราะห์ข้อมูลต้องการแดชบอร์ดที่ประมวลผลคำสั่งซื้อ, มูลค่าสินค้า, และยอดขายได้อย่างรวดเร็ว โดยคำสั่ง Query ต้องเข้าใจง่าย
- **การตัดสินใจ (Decision):** ออกแบบ Gold Layer ด้วย **Star Schema**:
  - `fact_sales`: บันทึก Granularity ระดับ Line Item ของคำสั่งซื้อพร้อม Metrics ทางการเงิน
  - `dim_customer`, `dim_product`, `dim_store`, `dim_date`: ตารางมิติอ้างอิง
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:* ประสิทธิภาพการรัน Aggregate Query (SUM, AVG) ร่วมกับ BI Tools สูงมาก, โครงสร้างเข้าใจง่ายสำหรับนักวิเคราะห์, ลดความซับซ้อนของ JOIN ข้ามหลายตาราง
  - *ข้อเสีย:* มี Data Redundancy สูงกว่า 3NF (Third Normal Form) เล็กน้อย และต้องจัดการ Surrogate Keys ในขั้นตอน ETL

---

### ADR 006: Pipeline Orchestration — Apache Airflow

- **บริบท (Context):** ระบบประกอบด้วย Task หลายขั้นตอน (Ingestion → Validation → Bronze Load → dbt Staging → dbt Marts → Quality Checks) ที่ต้องรันตามลำดับและมี Dependency ที่เข้มงวด
- **การตัดสินใจ (Decision):** ใช้ **Apache Airflow**
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:* มีระบบ Web UI ละเอียด, จัดการ Task Dependencies ผ่าน Directed Acyclic Graphs (DAG), มีระบบ Auto-Retry และ Alerting เมื่อล้มเหลว, รองรับ Idempotent Execution และ Backfilling
  - *ข้อเสีย:* การรัน Airflow บนเครื่อง Local กิน RAM พอสมควร (ต้องการอย่างน้อย 2-4 GB สำหรับ Scheduler และ Webserver)

---

### ADR 007: Processing Strategy — Incremental Processing with Watermark

- **บริบท (Context):** ระบบอีคอมเมิร์ซมีธุรกรรมใหม่เกิดขึ้นตลอดเวลา การ Full-load หรือคำนวณใหม่ทั้งตารางทุกวันจะสิ้นเปลืองทรัพยากรและใช้เวลานานขึ้นเรื่อยๆ ตามปริมาณข้อมูล
- **การตัดสินใจ (Decision):** ออกแบบระบบประมวลผลแบบ **Incremental Processing** โดยใช้ `updated_at` / Watermark Timestamp
- **สิ่งที่ต้องแลกเปลี่ยน (Trade-offs):**
  - *ข้อดี:* ลดเวลา Execution Time ลงอย่างมหาศาล, ประหยัดทรัพยากร I/O และ Compute
  - *ข้อเสีย:* ต้องออกแบบตรรกะ Upsert/Merge อย่างรอบคอบเพื่อป้องกันปัญหาข้อมูลไม่สอดคล้องกัน (Out-of-order data หรือ Late-arriving events)
