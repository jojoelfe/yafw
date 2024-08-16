import typer
from pathlib import Path
from yafw.project_management import Context, Global
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
    from yafw.project_management import FrealignProject, FrealignBinnedStack

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
    ctx: Context,
    bin: int = typer.Argument(..., help="Factor to bin by"),
):
    if ctx.obj is None:
        typer.echo("Please run in a FREALIGN project folder. Exiting.")
        raise typer.Exit(code=1)
    
    from pycistem.programs.resample import ResampleParameters, run
    import mrcfile
    from yafw.project_management import FrealignBinnedStack

    with mrcfile.open(ctx.obj.project.stacks[0].filename, mode="r") as f:
        orig_size = f.header.nx
    bin_to = round(orig_size / bin)
    output_filename = ctx.obj.project.path / f"{ctx.obj.project.name}B{bin}.mrc"
    if output_filename.exists():
        typer.echo(f"{output_filename} already exists. Exiting.")
        raise typer.Exit(code=1)
    par = ResampleParameters(
        input_filename=str(ctx.obj.project.stacks[0].filename),
        output_filename=str(output_filename),
        new_x_size=bin_to,
        new_y_size=bin_to,
    )
    print(f"Creating binned stack {output_filename}")
    run(par)
    ctx.obj.project.stacks.append(FrealignBinnedStack(
        filename=output_filename,
        pixel_size_A=ctx.obj.project.stacks[0].pixel_size_A * (orig_size / bin_to)
    ))
    ctx.obj.project.save()

@app.command()
def create_job(
    ctx: Context,
    stack: Path = typer.Argument(..., help="The stack to use"),
    starting_parameters: str = typer.Argument("default", help="Path to the starting parameters file"),
    parameter_mask: str = typer.Option("0 0 0 0 0", help="Path to the mask file"),
    nclasses: int = typer.Option(10, help="Number of classes to refine"),
    nprocessor_ref: int = typer.Option(10, help="Number of processors to use for refinement"),
    nprocessor_rec: int = typer.Option(10, help="Number of processors to use for reconstruction"),
    nrounds: int = typer.Option(10, help="Number of rounds to run"),
    outer_radius: float = typer.Option(200.0, help="Outer radius of the mask"),
    mol_mass: float = typer.Option(3000.0, help="Molecular mass of the particle"),
):
    if ctx.obj is None:
        typer.echo("Please run in a FREALIGN project folder. Exiting.")
        raise typer.Exit(code=1)
    from yafw.project_management import FrealignJob, FrealignParameters
    from shutil import copy
    job_id = max([job.id for job in ctx.obj.project.jobs], default=0) + 1
    job = FrealignJob(
        id=job_id,
        path=ctx.obj.project.path / f"job{job_id:04d}"
    )
    job.path.mkdir()
    if starting_parameters == "default":
        copy(ctx.obj.project.path / f"{ctx.obj.project.name}.par", job.path / f"{ctx.obj.project.name}_1_r1.par")
    else:
        copy(starting_parameters, job.path / f"{ctx.obj.project.name}_1_r1.par")
    stack_info = list(filter(lambda x: x.filename.absolute() == stack.absolute(),ctx.obj.project.stacks))[0]
    
    parameters = FrealignParameters(
        parameter_mask=parameter_mask,
        nclasses=nclasses,
        nprocessor_ref=nprocessor_ref,
        nprocessor_rec=nprocessor_rec,
        start_process=2,
        end_process=2 + nrounds - 1,
        data_input=ctx.obj.project.name,
        raw_images=str(stack.absolute()),
        outer_radius=outer_radius,
        mol_mass=mol_mass,
        pix_size = stack_info.pixel_size_A,
        dstep=(ctx.obj.project.detector_pixelsize_A * (stack_info.pixel_size_A / ctx.obj.project.original_pixelsize_A))/10000,
    )
    parameters.render(job.path / "mparameters")
    ctx.obj.project.jobs.append(job)
    ctx.obj.project.save()

@app.command()
def merge_classes(
    files: list[str] = typer.Argument(..., help="List of .par files to merge"),
    out_prefix: str = typer.Argument(..., help="Output prefix for the merged file without extention"),
    threshold: int = typer.Option(None, help="Occupancy threshold for filtering particles")
):
    import pandas as pd

    if threshold is None:
        threshold = 50 #Default value

    dataframes = {}
    for file in files:
        file_key = file.split('/')[-1].split('.')[0]
        dataframes[file_key] = pd.read_table(file, sep="\s+", comment="C", header=None)
    column_11_values = {}
    for key, df in dataframes.items():
        column_11_values[key] = df[11].values
        
    values_df = pd.DataFrame(column_11_values)

    values_df['sum'] = values_df.sum(axis=1)
    val_df = values_df[values_df['sum'] >= threshold].copy()
    val_df['max'] = val_df.iloc[:,:-1].idxmax(axis=1)

    # Code for threshold before sum Occupancy
    #values_df["treshold"] = values_df.max(axis=1)
    #val_df = values_df[values_df["treshold"] >= threshold].copy()
    #val_df["sum"] = val_df.iloc[:,:-1].sum(axis=1)
    #val_df['max'] = val_df.iloc[:,:-2].idxmax(axis=1)
    
    val_df["index"] = val_df.index.to_series()+1
    
    grouped_data = val_df[["sum", 'max', 'index']].groupby('max').agg(list).reset_index()
    
    output_df = {}
    for key in grouped_data.itertuples():
        df = dataframes[key.max].copy()
        df_ = df[df[0].isin(key.index)].copy()
        df_.loc[:, 11] = key.sum
        output_df[key.max] = df_
        
    output = pd.concat(output_df.values())
    output = output.drop_duplicates(subset=[0])
    output = output.sort_values(by=[0])
    
    with open(out_prefix+".par", "w") as f:
        for particle in output.itertuples():
            f.write("%7d%8.2f%8.2f%8.2f%10.2f%10.2f%8d%6d%9.1f%9.1f%8.2f%8.2f%10d%11.4f%8.2f%8.2f\n" % (
                int(particle._1),
                float(particle._2),
                float(particle._3),
                float(particle._4),
                float(particle._5),
                float(particle._6),
                int(particle._7),
                int(particle._8),
                float(particle._9),
                float(particle._10),
                float(particle._11),
                float(particle._12),
                int(particle._13),
                float(particle._14),
                float(particle._15),
                float(particle._16)))


@app.command()
def convertpar2star (
    parfile: Path = typer.Argument(..., help=".par file to convert to .star"),
    parent_starfile : Path = typer.Argument(..., help=" Refined parent .star file, converted from cistem bineries"),
    star_output : str = typer.Argument(..., help=" root output name of the new star file, has .star by default")
):
    import pandas as pd
    import starfile

    df = pd.read_table(parfile, sep="\s+", comment="C", header=None)
    star_df = starfile.read(parent_starfile)

    new_star = star_df[star_df.index.isin(df[0].values-1)]
    starfile.write(new_star, f'{star_output}.star')

@app.command()
def convert2rlnstar (
    cisTEMstar: Path = typer.Argument(..., help="cisTEM star file to convert"),
    stack_path: str = typer.Argument(..., help='Path for the particles stack, white particles'), #normalized and converted using cisTEM
    rlnstar_output: str = typer.Argument(..., help=" root output name of the rln star file, has .star by default")
):
    import pandas as pd
    import starfile

    cistem_star = starfile.read(cisTEMstar)
    
    new_vals = []
    for i in cistem_star['cisTEMPositionInStack'].values:
        new_vals.append("{:06d}@{}".format(i, stack_path))
    cistem_star["rlnImageName"] = new_vals

    new_column_order= ['rlnImageName','cisTEMDefocus1', 'cisTEMDefocus2', 'cisTEMDefocusAngle', 'cisTEMPhaseShift', 'cisTEMMicroscopeVoltagekV', 'cisTEMMicroscopeCsMM', 'cisTEMAmplitudeContrast','cisTEMPixelSize', 'cisTEMAnglePhi', 'cisTEMAngleTheta', 'cisTEMAnglePsi', 'cisTEMXShift', 'cisTEMYShift' ]
    new_star = cistem_star[new_column_order]
    relion_columns = new_star.rename(columns = {'rlnImageName':'rlnImageName', 'cisTEMDefocus1':'rlnDefocusU', 'cisTEMDefocus2':'rlnDefocusV', 'cisTEMDefocusAngle': 'rlnDefocusAngle', 'cisTEMPhaseShift': 'rlnPhaseShift', 'cisTEMMicroscopeVoltagekV':'rlnVoltage', 'cisTEMMicroscopeCsMM': 'rlnSphericalAberration', 'cisTEMAmplitudeContrast': 'rlnAmplitudeContrast', 'cisTEMPixelSize': 'rlnDetectorPixelSize','cisTEMAnglePhi':'rlnAngleRot', 'cisTEMAngleTheta': 'rlnAngleTilt', 'cisTEMAnglePsi': 'rlnAnglePsi', 'cisTEMXShift': 'rlnOriginXAngst','cisTEMYShift': 'rlnOriginYAngst'})
    row_count = len(relion_columns)
    columns2add = pd.DataFrame({
            'rlnMicrographName':['unkown.mrc']*row_count,
            'rlnCoordinateX' : ['0.000000']*row_count,
            'rlnCoordinateY' : ['0.000000']*row_count,
            'rlnMagnification': ['10000.000000']*row_count 
            })
    complete_star = relion_columns.join(columns2add)
    sorted_column_order = ['rlnMicrographName', 'rlnCoordinateX', 'rlnCoordinateY', 'rlnImageName', 'rlnDefocusU', 'rlnDefocusV', 'rlnDefocusAngle', 'rlnPhaseShift', 'rlnVoltage', 'rlnSphericalAberration', 'rlnAmplitudeContrast', 'rlnMagnification', 'rlnDetectorPixelSize', 'rlnAngleRot', 'rlnAngleTilt', 'rlnAnglePsi', 'rlnOriginXAngst', 'rlnOriginYAngst'] 
    sorted_relion_star = complete_star[sorted_column_order]
    starfile.write(sorted_relion_star, rlnstar_output)

@app.command()
def fsc_results(ctx: Context):
    from yafw.frealign_jobs import parse_job
    if ctx.obj is None or ctx.obj.job is None:
        typer.echo("Please run in a FREALIGN job folder. Exiting.")
        raise typer.Exit(code=1)
    job_data = parse_job(ctx.obj.project, ctx.obj.job)
    #print(job_data[0][-1])
    import matplotlib.pyplot as plt
    import matplotlib.ticker as tick
    import numpy as np
    for i, class_list in enumerate(job_data):
        last_round = class_list[-1]
        resolution = last_round.FSC.resolution
        FSC_values = last_round.FSC.fsc_values
        data_tuples = list(zip(resolution, FSC_values))
        value_found = False

        for resolution, fsc_value in data_tuples:
            if fsc_value <= 0.143:
                print(f"Resolution: {resolution}, FSC Value: {fsc_value}, Class {i+1}")
                value_found = True

        if not value_found:
            print(f"No value <= 0.143 in the Class {i+1}")

    def on_legend_click(event):
        legend = event.artist
        index = event.ind[0]
        line = legend.get_lines()[index]
        line.set_visible(not line.get_visible())
        plt.draw()
   
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for i, class_list in enumerate(job_data):
        last_round = class_list[-1]
        number_values = len(last_round.FSC.resolution)
        ax.plot(range(number_values),last_round.FSC.fsc_values,label=f"Class {i+1}")
        
        plt.xlim(number_values-1,0)
        plt.ylim(-0.01,1.05)
        def x_fmt(x, y):
            if x>number_values-1:
                return ""
            return last_round.FSC.resolution[int(x)]
    ax.xaxis.set_major_formatter(tick.FuncFormatter(x_fmt))
    plt.axhline(0.143, color="black", ls=":")
    plt.xlabel('Resolution (Å)')
    plt.ylabel('FSC')
    legend = plt.legend()
    #plt.legend()
    plt.gcf().canvas.mpl_connect('pick_event', on_legend_click)
    plt.show()

    fig2 = plt.figure()
    ax = fig2.add_subplot(111)
    for i, class_list in enumerate(job_data):
        last_round = class_list[-1]
        number_values = len(last_round.FSC.resolution)
        ax.plot(range(number_values),last_round.FSC.part_fsc_values,label=f"Class {i+1}")
        
        plt.xlim(number_values-1,0)
        plt.ylim(-0.01,1.05)
        def x_fmt(x, y):
            if x>number_values-1:
                return ""
            return last_round.FSC.resolution[int(x)]
    ax.xaxis.set_major_formatter(tick.FuncFormatter(x_fmt))
    plt.axhline(0.143, color="black", ls=":")
    plt.xlabel('Resolution (Å)')
    plt.ylabel('Part_FSC')
    plt.legend()
    plt.show()  

@app.command()
def job_status(ctx: Context, until_round:int = -1):
    from yafw.frealign_jobs import parse_job
    if ctx.obj is None or ctx.obj.job is None:
        typer.echo("Please run in a FREALIGN job folder. Exiting.")
        raise typer.Exit(code=1)
    job_data = parse_job(ctx.obj.project, ctx.obj.job)
    import matplotlib.pyplot as plt
    for class_n in range(job_data[-1][until_round].class_n):
        data = job_data[class_n]
        plt.plot([d.round for d in data], [d.avg_occ for d in data], label=f"Class {class_n+1}")
    plt.legend()
    plt.show()

@app.callback()
def main(
    ctx: Context,
):
    from yafw.project_management import FrealignProject, FrealignJob
    if (Path.cwd() / f"{Path.cwd().name}.json").exists():
        ctx.obj = Global(project=FrealignProject.open(f"{Path.cwd() / Path.cwd().name}.json"),job=None)
    elif (Path.cwd().parent / f"{Path.cwd().parent.name}.json").exists():
        project = FrealignProject.open(f"{Path.cwd().parent / Path.cwd().parent.name}.json")
        job = list(filter(lambda x: x.path.absolute() == Path.cwd().absolute(),project.jobs))
        if len(job) == 1:
            job = job[0]
        else:
            job = FrealignJob(
                id=0,
                path=Path.cwd()
            )
        ctx.obj = Global(project=project,
                         job=job)
    else:
        project = None
        job = FrealignJob(
                id=0,
                path=Path.cwd()
            )
        ctx.obj = Global(project=project,
                         job=job)


@app.command()
def continue_job(ctx: Context, nrounds: int = typer.Argument(1, help="Number of rounds to continue")):
    from yafw.frealign_jobs import continue_job
    if ctx.obj is None or ctx.obj.job is None:
        typer.echo("Please run in a FREALIGN job folder. Exiting.")
        raise typer.Exit(code=1)
    continue_job(ctx.obj.project, ctx.obj.job, nrounds=nrounds)

@app.command()
def combine_classes(ctx: Context,
                    name: str = typer.Argument(..., help="Name of the new particle set"),
                    job_id: int = typer.Argument(..., help="Job ID to combine classes from"),
                    class_numbers: list[str] = typer.Argument(..., help="Class numbers to combine"),
                    iteration: int = typer.Option(-1, help="Iteration number to combine classes from, -1 is the latest")):
    
    from yafw.frealign_jobs import combine_classes
    if ctx.obj is None:
        typer.echo("Please run in a FREALIGN project folder. Exiting.")
        raise typer.Exit(code=1)
    job = list(filter(lambda x: x.id == job_id, ctx.obj.project.jobs))[0]
    combine_classes(project=ctx.obj.project, name=name, job=job, class_numbers=class_numbers, iteration=iteration)
    


if __name__ == "__main__":
    app()

