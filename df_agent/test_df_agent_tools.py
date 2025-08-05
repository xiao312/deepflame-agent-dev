from df_agent_tools import check_bashrc_loaded, run_allrun_script, read_and_save_openfoam_scalars, plot_openfoam_data

print(check_bashrc_loaded())

print(run_allrun_script("/home/xk/Software/6_bohr_agent/cases/oneD_freelyPropagation/H2"))

print(read_and_save_openfoam_scalars("/home/xk/Software/6_bohr_agent/cases/oneD_freelyPropagation/H2/0.002", "files/T-Cx.txt"))

print(plot_openfoam_data("files/T-Cx.txt"))