"""테스트 패키지.

저장소의 src/ 폴더를 sys.path 맨 앞에 넣습니다. 그래서 패키지를 설치하지 않아도
저장소 뿌리에서 `python3 -m unittest discover -s tests -t .` 가 바로 돕니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)
