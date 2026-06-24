# IVUS Tools

## 1. 摘要說明

IVUS Tools 是一套研究導向的 IVUS（Intravascular Ultrasound，血管內超音波）DICOM 前處理工具，主要用於多影格 cine DICOM 的轉檔、影格匯出、詮釋資料擷取、批次處理，以及後續 MedSAM2 分割流程整合。

功能包含：

- 將 IVUS DICOM 轉成 MP4，並優先維持 DICOM 內記錄的原始禎率。
- 將 DICOM 匯出為連續 PNG 影格，檔名自動補零，適合標註與 MedSAM2 流程。
- 將 PNG 影格序列重新合成 MP4。
- 擷取 DICOM 詮釋資料，包含影像尺寸、影格數、禎率來源、Study Time、Institution Name、Manufacturer Model Name 等資訊。
- DICOM 轉 MP4 時可將指定 DICOM tag 寫入 MP4 詮釋資料。
- 批次轉換資料夾內的 DICOM 檔案，並保留逐檔成功或失敗結果。
- 長時間轉檔時顯示進度條，也可用參數關閉。
- 轉檔完成後會在終端機列出結果摘要，並可輸出 JSON 報告供後續追蹤。
- 預設將 DICOM 轉 MP4 的輸出集中放在 `outputs/mp4/`，避免根目錄堆積轉檔產物。

MP4 內可寫入的 DICOM tag：

- `StudyTime` 寫入為 `study_time`
- `InstitutionName` 寫入為 `institution_name`
- `ManufacturerModelName` 寫入為 `manufacturer_model_name`

`PatientID` 預設不會寫入 MP4 詮釋資料；完整詮釋資料會保存在附屬 JSON 檔案中。

## 2. 開發環境

建議使用 Python 3.10 以上版本。本專案目前已在 Python 3.10 與 Python 3.11 上執行測試。

安裝套件：

```bash
pip install -r requirements.txt
```

若要以可編輯模式開發：

```bash
pip install -e .
```

主要依賴套件：

- `pydicom`：讀取 DICOM 檔案與詮釋資料。
- `opencv-python`：寫出 MP4 影片。
- `numpy`：處理影像陣列。
- `pillow`：輸出 PNG 影格。
- `tqdm`：顯示進度條。
- `click`：建立 CLI 命令列介面。

若系統已安裝 `ffmpeg`，DICOM 轉 MP4 時會嘗試將指定 DICOM tag 寫入 MP4 容器詮釋資料。若未安裝 `ffmpeg`，影片轉檔仍會完成，JSON 報告會記錄 MP4 詮釋資料寫入已略過。

開發與驗證常用命令：

```bash
pytest -q
flake8 .
black --check .
isort --check-only .
```

## 3. 執行命令

### DICOM 轉 MP4

不指定輸出路徑時，MP4 與相關 JSON 會預設輸出到 `outputs/mp4/`：

```bash
python dicom_to_mp4.py \
  -i study.dcm
```

輸出範例：

```text
outputs/mp4/study.mp4
outputs/mp4/study.metadata.json
outputs/mp4/study.conversion-report.json
```

若要指定輸出路徑，使用 `-o` 或 `--output`：

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  -o study.mp4
```

常用參數：

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  -o study.mp4 \
  --fps 20 \
  --codec mp4v \
  --report study.conversion-report.json
```

DICOM 轉 MP4 的禎率判斷優先順序：

1. 使用者指定的 `--fps`
2. DICOM `CineRate`
3. DICOM `RecommendedDisplayFrameRate`
4. DICOM `FrameTime`，以 `1000 / FrameTime` 換算
5. 找不到可用資訊時才使用備用禎率

關閉 MP4 詮釋資料寫入：

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  -o study.mp4 \
  --no-embed-metadata
```

關閉進度條：

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  --no-progress
```

### DICOM 轉 PNG 影格序列

```bash
python dicom_to_png.py \
  -i study.dcm \
  -o frames/
```

輸出影格會依原始順序排列，並使用補零檔名：

```text
00000.png
00001.png
00002.png
```

預設會寫出：

```text
frames/conversion-report.json
```

### PNG 影格序列轉 MP4

```bash
python png_to_mp4.py \
  -i frames/ \
  -o video.mp4 \
  --fps 20
```

PNG 影格資料夾本身不含 DICOM 禎率資訊，因此需要特定播放速度時請明確指定 `--fps`。若省略，預設值為 `30.0`。

### 擷取 DICOM 詮釋資料

在終端機印出詮釋資料：

```bash
python extract_metadata.py -i study.dcm
```

寫出成 JSON 檔案：

```bash
python extract_metadata.py \
  -i study.dcm \
  -o metadata.json
```

### 批次 DICOM 轉 MP4

```bash
python batch_convert.py \
  --input-dir dicom/ \
  --output-dir mp4/
```

遞迴處理子資料夾：

```bash
python batch_convert.py \
  --input-dir dicom/ \
  --output-dir mp4/ \
  --recursive
```

批次轉檔會顯示檔案層級進度，單一檔案失敗時會盡量繼續處理其他檔案，並寫出：

```text
mp4/batch-conversion-report.json
```

### 產生測試用合成 DICOM

專案內提供非病患資料的合成 IVUS-like DICOM 產生器，可用於本機快速測試。

```bash
python examples/create_synthetic_dicom.py \
  -o examples/synthetic_ivus.dcm \
  --frames 24 \
  --rows 128 \
  --columns 128 \
  --fps 20
```

完整測試流程範例：

```bash
python dicom_to_png.py \
  -i examples/synthetic_ivus.dcm \
  -o examples/frames/

python dicom_to_mp4.py \
  -i examples/synthetic_ivus.dcm \
  -o examples/synthetic_ivus.mp4
```

### 報告與結果清單

轉檔命令預設會在終端機印出完成摘要，並產生 JSON 報告。可用 `--report` 指定報告路徑：

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  --report reports/study.conversion-report.json
```

若不需要寫出報告：

```bash
python dicom_to_mp4.py \
  -i study.dcm \
  --no-report
```

### MedSAM2 流程建議

若要接 MedSAM2 分割流程，建議使用 PNG 影格序列而不是 MP4：

```text
DICOM -> PNG Sequence -> MedSAM2 -> Tracking -> Masks -> Video Overlay
```

PNG 影格序列可避免 MP4 壓縮失真，並保留穩定的影格順序，較適合標註、分割與追蹤流程。

## 4. 項目checklist

- [x] 建立可重用的 `ivus_tools` Python package。
- [x] 實作 DICOM 轉 MP4。
- [x] DICOM 轉 MP4 時預設輸出到 `outputs/mp4/`。
- [x] DICOM 轉 MP4 時維持原始禎率，並記錄 fps 來源。
- [x] DICOM 轉 MP4 時支援進度條。
- [x] DICOM 轉 MP4 時支援附屬詮釋資料 JSON。
- [x] DICOM 轉 MP4 時支援轉檔報告 JSON。
- [x] DICOM 轉 MP4 時支援將 `StudyTime`、`InstitutionName`、`ManufacturerModelName` 寫入 MP4 詮釋資料。
- [x] 實作 DICOM 轉 PNG 影格序列。
- [x] 實作 PNG 影格序列轉 MP4。
- [x] 實作 DICOM 詮釋資料擷取。
- [x] 實作批次 DICOM 轉 MP4。
- [x] 批次轉檔支援完成結果清單與 JSON 報告。
- [x] 建立合成 DICOM 範例產生器。
- [x] 建立 pytest 測試。
- [x] 建立 GitHub Actions CI。
- [ ] 加入公開可分享的範例影像、截圖或 GIF。
- [ ] 加入更完整的 MedSAM2 整合範例。
