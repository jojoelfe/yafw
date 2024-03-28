from yafw.project_management import FrealignJob, FrealignProject, FrealignParameters
from pathlib import Path
import re
from pydantic import BaseModel
import os

#https://stackoverflow.com/questions/2301789/how-to-read-a-file-in-reverse-order
def reverse_readline(filename, buf_size=8192):
    """A generator that returns the lines of a file in reverse order"""
    with open(filename, 'rb') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            # remove file's last "\n" if it exists, only for the first buffer
            if remaining_size == file_size and buffer[-1] == ord('\n'):
                buffer = buffer[:-1]
            remaining_size -= buf_size
            lines = buffer.split('\n'.encode())
            # append last chunk's segment to this chunk's last line
            if segment is not None:
                lines[-1] += segment
            segment = lines[0]
            lines = lines[1:]
            # yield lines in this chunk except the segment
            for line in reversed(lines):
                # only decode on a parsed line, to avoid utf-8 decode error
                yield line.decode()
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment.decode()



class FSCCurve(BaseModel):
    ring_radius: list[float] = []
    resolution: list[float]= []
    fsc_values: list[float]= []
    part_fsc_values: list[float] = []

class FrealignResults(BaseModel):
    round: int
    class_n: int
    avg_occ: float = None
    avg_score: float = None
    FSC: FSCCurve = FSCCurve()



def continue_job(project: FrealignProject, job: FrealignJob, nrounds: int = 1):
    import shutil
    current_params = FrealignParameters.open(job.path / "mparameters")
    shutil.copy(job.path / "mparameters", job.path / f"mparameters_{current_params.start_process}_{current_params.end_process}")
    current_params.start_process = current_params.end_process + 1
    current_params.end_process = current_params.start_process + nrounds - 1 
    current_params.render(job.path / "mparameters")

def parse_job(project: FrealignProject, job: FrealignJob):
    from rich.progress import track
    par_files = list(job.path.glob(f"*.par"))
    results = []
    for par_file in track(par_files):
        if project is None:
            regexp = re.compile(r".+_(\d+)_r(\d+).par")
        else :
            regexp = re.compile(f"{project.name}_(\d+)_r(\d+).par")        
        match = re.match(regexp, par_file.name)

        if match:
            round_n = int(match.group(1))
            class_n = int(match.group(2))
            result = FrealignResults(round=round_n, class_n=class_n)
            results.append(result)
            # Read the par file and extract the occupancy values
            read_state = "NONE"
            for line in reverse_readline(par_file):
                if not line.startswith("C"):
                    break
                if line.startswith("C  Average"):
                    read_state = "FSC"
                    continue
                if line.startswith("C  NO"):
                    read_state = "NONE"
                    continue
                if line.startswith("C  Total"):
                    splitline = line.split()
                    result.avg_score = float(splitline[-2])
                    result.avg_occ = float(splitline[-1])
                    continue
                if read_state == "FSC":
                    splitline = line.split()
                    result.FSC.ring_radius.append(float(splitline[3]))
                    result.FSC.resolution.append(float(splitline[2]))
                    result.FSC.fsc_values.append(float(splitline[5]))
                    result.FSC.part_fsc_values.append(float(splitline[6]))
                    continue
    results.sort(key=lambda x: (x.round, x.class_n))
    per_class_results = []
    for class_n in range(1, results[-1].class_n+1):
        round_results = [result for result in results if result.class_n == class_n]
        per_class_results.append(round_results)
    return per_class_results