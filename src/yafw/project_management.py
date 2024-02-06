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
    project: Optional[FrealignProject]
    job: Optional[FrealignJob]
    

class Context(typer.Context):
    obj: Optional[Global] = None

class FrealignParameters(BaseModel):
    cluster_type: str = "none"
    nprocessor_ref: int = 10
    nprocessor_rec: int = 10
    mem_per_cpu: int = 2048
    MODE: int = 1
    start_process: int = 2
    end_process: int = 10
    res_high_refinement: float = 16.0
    res_high_class: float = 16.0
    nclasses: int = 10
    data_input: str = "stack"
    raw_images: str = "stack.mrc"
    image_contrast: str = "N"
    outer_radius: float = 200.0
    inner_radius: float = 0.0
    mol_mass: float = 1000
    Symmetry: str = "C1"
    pix_size: float = 8.0
    dstep: float = 37.7
    Aberration: float = 2.7
    Voltage: float = 300.0
    Amp_contrast: float = 0.07
    mask_file: str = ""
    mask_edge: int = 5
    mask_outside_weight: float = 0.0
    mask_filt_res: float = 0.0
    mask_filt_edge: int = 5
    focus_mask: str = ""
    DANG: float = 0.0
    parameter_mask: str = "0 0 0 0 0"
    refineangleinc: int = 4
    refineshiftinc: int = 4
    res_reconstruction: float = 0.0
    res_low_refinement: float = 50.0
    thresh_reconst: float = 0.0
    nbootstrap: int = 1000
    FDEF: str = 'F'
    FMATCH: str = 'F'
    FBOOST: str = 'T'
    mp_cpus: int = 1
    restart_after_crash: str = 'F'
    delete_scratch: str = 'T'
    qsub_string_ref: str = ""
    qsub_string_rec: str = ""
    first_particle: str = ""
    last_particle: str = ""
    frealign_bin_dir: str = ""
    scratch_dir: str = ""
    ITMAX: int = 200
    XSTD: float = 0.0
    PBC: float = 2.0
    thresh_refine: float = 50.0
    RBfactor: float = 0.0
    FMAG: str = 'F'
    FASTIG: str = 'F'
    FPART: str = 'F'
    FFILT: str = 'T'
    FBEAUT: str = 'F'
    beam_tilt_x: float = 0.0
    beam_tilt_y: float = 0.0
    BSC: float = 2.0
    percentage: float = 1.0
    normalize_images: str = 'F'
    crop_images: str = 'F'
    adjust_scores: str = 'T'
    search_mask_radius: float = 0.0
    search_range_x: float = 0.0
    search_range_y: float = 0.0
    boost_limit: float = 0.0
    P3Dblurring: str = 'F'
    even_odd_fsc: str = 'T'

    def render(self, filename):
        with open(filename, "w") as f:
            for k, v in self.model_dump().items():
                if k in ["parameter_mask", "focus_mask"]:
                    f.write(f'{k}\t\t"{v}"\n')
                else:
                    f.write(f'{k}\t\t{v}\n')
    
    @classmethod
    def open(cls, filename):
        with open(filename, "r") as f:
            data = f.readlines()
        out = cls()
        for line in data:
            k, v, *_ = line.split("")
            setattr(out, k, v)
        return out
            