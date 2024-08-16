## Tested on fsc_results
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
    '''
    #print(range(len(job_data[0][-1].FSC.fsc_values)))
    #print(((job_data[0][-1].FSC.resolution)),job_data[0][-1].FSC.fsc_values)
    #typer.echo("Resolution")
    resolution = (job_data[0][-1].FSC.resolution)
    #print(resolution)
    #typer.echo("FSC")
    FSC_values = (job_data[0][-1].FSC.fsc_values)
    #print(FSC_values)
    data_tuples = list(zip(resolution,FSC_values))
    #print(data_tuples)
    value_found = False
    for resolution, fsc_value in data_tuples:
        if fsc_value <= 0.143:
            print(f"Resolution: {resolution}, FSC Value: {fsc_value}")
            value_found = True
    if not value_found:
        print("No value <= 0.143 in your list")

    for i, class_list in enumerate(job_data):
         last_round = class_list[-1]
         resolution = (last_round.FSC.resolution)
         FSC_values = (last_round.FSC.fsc_values)
         data_tuples = list(zip(resolution,FSC_values))
         value_found = False
        for resolution, fsc_value in data_tuples:
                if fsc_value <= 0.143:
                print(f"Resolution: {resolution}, FSC Value: {fsc_value}")
                value_found = True
                if not value_found:
                print("No value <= 0.143 in your"f"Class {i+1}")
    '''     
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
    plt.legend()
    plt.show()
    
    fig2 = plt.figure()
    ax = fig2.add_subplot(111)
    ax.plot(range(len(job_data[0][-1].FSC.resolution)),job_data[0][-1].FSC.part_fsc_values)
    plt.xlim(len(job_data[0][-1].FSC.resolution)-1,0)
    plt.ylim(-0.01,1.05)
    def x_fmt(x, y):
        if x>len(job_data[0][-1].FSC.resolution)-1:
            return ""
        return job_data[0][-1].FSC.resolution[int(x)]

    ax.xaxis.set_major_formatter(tick.FuncFormatter(x_fmt))
    plt.axhline(0.143, color="black", ls=":")
    plt.xlabel('Resolution (Å)')
    plt.ylabel('Part_FSC')
    plt.show()
   
'''
slices = job_data[0]
# Create a figure and axes
fig, ax = plt.subplots()
# Iterate over slices and plot each one
for slice_data in slices:
    x_values = range(len(slice_data[-1].FSC.resolution))
    y_values = slice_data[-1].FSC.fsc_values
    ax.plot(x_values, y_values, label=f"Slice {len(ax.lines) + 1}")
    plt.xlim(len(job_data[0,1][-1].FSC.resolution)-1,0)
    plt.ylim(-0.01,1.05)
    def x_fmt(x, y):
        if x>len(job_data[0,1][-1].FSC.resolution)-1:
            return ""
        return job_data[0][-1].FSC.resolution[int(x)]
    ax.xaxis.set_major_formatter(tick.FuncFormatter(x_fmt))
    plt.axhline(0.143, color="black", ls=":")
    plt.xlabel('Resolution (Å)')
    plt.ylabel('FSC')
    plt.show()
'''