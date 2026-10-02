# 🚀 E-commerce End-to-End Data Platform

Production-grade Data Engineering Platform สำหรับธุรกิจ E-commerce ออกแบบตามสถาปัตยกรรม Medallion Architecture (Bronze / Silver / Gold) และหลักการ Modern Data Stack (MDS) รันได้แบบ 100% Reproducible ผ่าน Docker Compose

---

## 1. ภาพรวมของโปรเจกต์ (Project Overview)
โปรเจกต์นี้จำลองและพัฒนาระบบคลังข้อมูลและการประมวลผลข้อมูลขนาดใหญ่แบบครบวงจร ตั้งแต่การดึงข้อมูลดิบ (Ingestion) จากระบบต้นทางเข้าสู่ Data Lake, การแปลงและทดสอบคุณภาพข้อมูลด้วย dbt, การจัดลำดับการทำงานด้วย Apache Airflow ไปจนถึงการแสดงผลผ่าน Metabase BI Dashboard

## 2. ปัญหาและบริบททางธุรกิจ (Business Scenario)
ธุรกิจอีคอมเมิร์ซมีธุรกรรมคำสั่งซื้อ ลูกค้า สินค้า และการชำระเงินเกิดขึ้นอย่างต่อเนื่อง แต่ทีมบริหารและนักวิเคราะห์ยังขาดมุมมองข้อมูลแบบรวมศูนย์ ทำให้ไม่สามารถตอบคำถามสำคัญทางธุรกิจได้อย่างทันท่วงที:
- รายได้และกำไรสุทธิต่อวัน/เดือนเติบโตอย่างไร?
- พฤติกรรมการซื้อซ้ำของลูกค้า (Customer Retention & Returning Customers) เป็นอย่างไร?
- สินค้าใดสร้างรายได้สูงสุด และหมวดหมู่ใดมียอดขายตกต่ำ?

## 3. แผนภาพสถาปัตยกรรม (Architecture Diagram)

```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Source Systems  │  ───> │ Data Ingestion  │  ───> │  Raw Data Lake  │
│ CSV / Mock API  │       │ (Python Script) │       │ (MinIO / S3)    │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                                                             ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  BI Dashboard   │  <─── │ Data Warehouse  │  <─── │ Orchestration   │
│   (Metabase)    │       │ (PostgreSQL/dbt)│       │(Apache Airflow) │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

## 4. เทคโนโลยีที่เลือกใช้ (Technology Stack)
- **Programming & Scripting:** Python 3.10, SQL
- **Data Ingestion & Storage:** MinIO (S3-compatible Object Storage)
- **Data Warehouse:** PostgreSQL 16
- **Data Transformation & Modeling:** dbt (data build tool)
- **Pipeline Orchestration:** Apache Airflow 2.8
- **Business Intelligence:** Metabase
- **Containerization & CI/CD:** Docker, Docker Compose, GitHub Actions
- **Testing & Code Quality:** pytest, dbt test, ruff

## 5. กระแสการไหลและเลเยอร์ของข้อมูล (Data Flow & Medallion Layers)
- **Bronze Layer (Raw):** จัดเก็บข้อมูลดิบในสภาพดั้งเดิม ไม่มีการแปลงหรือกรองตรรกะทางธุรกิจ
- **Silver Layer (Cleaned & Standardized):** คัดกรองข้อมูลซ้ำซ้อน (Deduplication), ตรวจสอบประเภทข้อมูล (Type Casting), แปลงเวลาเป็น ISO UTC
- **Gold Layer (Analytical Marts):** Star Schema ที่รวมข้อมูลระดับคำสั่งซื้อและมิติข้อมูลพร้อมสำหรับการวิเคราะห์

## 6. ตัวแบบข้อมูล (Data Model — Star Schema)
- **Fact Table:** `fact_sales` (order_id, customer_key, product_key, store_key, date_key, quantity, unit_price, discount, revenue, cost, profit)
- **Dimension Tables:**
  - `dim_customer`
  - `dim_product`
  - `dim_store`
  - `dim_date`

## 7. วิธีการติดตั้งและรันโปรเจกต์ (How to Run)

### สิ่งที่ต้องมีก่อนเริ่ม (Prerequisites):
- Docker Desktop (พร้อมใช้งาน Docker Compose)
- Python 3.10+ (สำหรับ Local Dev / Testing)

### ขั้นตอนการรัน:
1. Clone repository และคัดลอกไฟล์ Environment Variables:
   ```bash
   cp .env.example .env
   ```
2. เริ่มต้นระบบทั้งหมดผ่าน Docker Compose:
   ```bash
   docker compose up -d
   ```
3. ตรวจสอบการทำงานของ Web Services:
   - **Airflow Web UI:** [http://localhost:8080](http://localhost:8080) (`airflow_admin` / `airflow_password_dev_123`)
   - **MinIO Console:** [http://localhost:9001](http://localhost:9001) (`minio_admin` / `minio_password_dev_123`)
   - **Metabase UI:** [http://localhost:3000](http://localhost:3000)
   - **PostgreSQL Warehouse:** `localhost:5432` (`dw_admin` / `dw_password_dev_123`, DB: `ecommerce_dw`)

## 8. การทดสอบและการรับประกันคุณภาพข้อมูล (Data Quality Strategy)
- **Unit Testing:** `pytest tests/` สำหรับฟังก์ชัน Ingestion และ Helper
- **dbt Data Testing:** ตรวจสอบ `unique`, `not_null`, `accepted_values`, และ Foreign Key `relationships`
- **Idempotency Guarantee:** รองรับการ Re-run Pipeline ซ้ำโดยไม่สร้างข้อมูลเบิ้ล

## 9. เอกสารอ้างอิงเพิ่มเติม
- [Architecture Decisions Record (ADR)](file:///docs/architecture-decisions.md)
