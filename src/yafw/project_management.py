from pydantic import BaseModel
from pathlib import Path

class FrealignBinnedStack(BaseModel):
    filename: Path
    pixel_size_A: float

class FrealignProject(BaseModel):
    name: str
    path: Path
    imported_starfile: Path
    imported_mrcfile: Path
    original_pixelsize_A: float
    detector_pixelsize_A: float = 50000.0
    stacks: list[FrealignBinnedStack] = []


    def save(self):
        with open(self.path / f"{self.name}.json", "w") as f:
            f.write(self.model_dump_json())