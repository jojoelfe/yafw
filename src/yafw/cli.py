import typer
from pathlib import Path

app = typer.Typer()

@app.command()
def create_project(
    starfilename: Path = typer.Argument(..., help="Path to the starfile"),
    mrcfilename: Path = typer.Argument(..., help="Path to the mrcfile"),
    name: str = typer.Argument("stack", help="Name of the project"),
    original_pixelsize: float = typer.Argument(..., help="Physical pixelsize that the data was collected at in Angstroms"),
    detector_pixelsize: float = typer.Option(50000.0, help="Physical pixelsize of the detector in Angstroms"),
):
    import starfile
    from shutil import copy
    from project_management import FrealignProject, FrealignBinnedStack

    project_dir = Path.cwd() / name
    project_dir.mkdir()
    copy(mrcfilename, project_dir/f"{name}.mrc")

    particle_data = starfile.read(starfilename)

    with open(project_dir / f"{name}.par", "w") as f:
        for i, particle in enumerate(particle_data.itertuples()):
            shift_x = 0.0
            shift_y = 0.0
            if hasattr(particle, "cisTEMShiftX"):
                shift_x = particle.cisTEMShiftX
                shift_y = particle.cisTEMShiftY
            f.write("%7d%8.2f%8.2f%8.2f%10.2f%10.2f%8d%6d%9.1f%9.1f%8.2f%8.2f%10d%11.4f%8.2f%8.2f\n" % (
                particle.cisTEMPositionInStack,
                particle.cisTEMAnglePsi,
                particle.cisTEMAngleTheta,
                particle.cisTEMAnglePhi,
                shift_x,
                shift_y,
                detector_pixelsize / original_pixelsize,
                1,
                particle.cisTEMDefocus1,
                particle.cisTEMDefocus2,
                particle.cisTEMDefocusAngle,
                100.0,
                0,
                0.5,
                0.0,
                0.0
            ))
    #"%7d%8.2f%8.2f%8.2f%10.2f%10.2f%8d%6d%9.1f%9.1f%8.2f%8.2f%10d%11.4f%8.2f%8.2f\n"
    # do something with the starfile and mrcfile
    project = FrealignProject(
        name=name,
        path=project_dir,
        imported_starfile=starfilename,
        imported_mrcfile=mrcfilename,
        original_pixelsize_A=original_pixelsize,
        detector_pixelsize_A=detector_pixelsize
    )

    project.stacks.append(FrealignBinnedStack(
        filename=project_dir / f"{name}.mrc",
        pixel_size_A=particle_data.cisTEMPixelSize[0]
    ))
    # Write the project to disk as json
    project.save()
    typer.echo(f"Created parfile {name}.par and stack {name}.mrc in {project_dir}")

@app.command()
def create_binned_stack(
    pixelsize: float = typer.Argument(..., help="Pixel size of the binned stack"),
):
    pass
if __name__ == "__main__":
    app()