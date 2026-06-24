from __future__ import annotations

import numpy as np
from PIL import Image

from ivus_tools.conversion import export_dicom_to_png


def test_export_dicom_to_png_preserves_order_and_zero_padding(
    tmp_path, make_test_dicom
) -> None:
    frames = np.stack(
        [
            np.full((4, 5), 10, dtype=np.uint8),
            np.full((4, 5), 80, dtype=np.uint8),
            np.full((4, 5), 200, dtype=np.uint8),
        ]
    )
    dicom_path = make_test_dicom(frames)
    output_dir = tmp_path / "frames"

    result = export_dicom_to_png(
        dicom_path,
        output_dir,
        digits=5,
        show_progress=False,
        write_report=False,
    )

    png_paths = sorted(output_dir.glob("*.png"))
    assert [path.name for path in png_paths] == ["00000.png", "00001.png", "00002.png"]
    assert [int(np.asarray(Image.open(path))[0, 0]) for path in png_paths] == [
        10,
        80,
        200,
    ]
    assert result["frames_processed"] == 3
    assert result["first_frame"] == "00000.png"
    assert result["last_frame"] == "00002.png"
