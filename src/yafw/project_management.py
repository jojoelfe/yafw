from pydantic import BaseModel
from pathlib import Path
import typer
from typing import Optional
from enum import Enum

class FrealignJobStatus(Enum):
    PREPARED = "prepared"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"

class FrealignBinnedStack(BaseModel):
    filename: Path
    pixel_size_A: float

class FrealignJob(BaseModel):
    id: int
    path: Path
    status: FrealignJobStatus = FrealignJobStatus.PREPARED

class FrealignProject(BaseModel):
    name: str
    path: Path
    imported_starfile: Path
    imported_mrcfile: Path
    original_pixelsize_A: float
    detector_pixelsize_A: float = 50000.0
    stacks: list[FrealignBinnedStack] = []
    jobs: list[FrealignJob] = []


    def save(self):
        with open(self.path / f"{self.name}.json", "w") as f:
            f.write(self.model_dump_json())
    
    @classmethod
    def open(cls, filename):
        with open(filename, "r") as f:
            data = f.read()
        return cls.model_validate_json(data)

class Global(BaseModel):
    project: FrealignProject
    

class Context(typer.Context):
    obj: Optional[Global] = None