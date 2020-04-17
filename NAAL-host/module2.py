def build_FpgaPesEnsembleNetwork(model, in_dimensions,output_dimensions,n_neurons,bias,neuron_type,scaled_encoders,synapse_tau):
    """Builder to integrate FPGA network into Nengo
    Add build steps like nengo?
    """
    # Collect the simulation argument values
    sim_args = {}
    sim_args["dt"] = model.dt

    # Collect the ensemble argument values
    ens_args = {}
    ens_args["in_dimensions"] = in_dimensions
    ens_args["output_dimensions"] = output_dimensions
    ens_args["n_neurons"] = n_neurons
    ens_args["bias"] = bias
    ens_args["neuron_type"]= neuron_type
    ens_args["scaled_encoders"] = scaled_encoders

    recur_args = {}
    recur_args["weights"] = 0  # Necessary as flag even if not used
        # Grab relevant attributes
    recur_args["tau"] = synapse_tau

    # Save the NPZ data file
    npz_filename = "fpen_args_" + str(id(network)) + ".npz"
    network.arg_data_file = npz_filename
    np.savez_compressed(
        network.local_data_filepath,
        sim_args=sim_args,
        ens_args=ens_args,
        conn_args=conn_args,
        recur_args=recur_args,
    )
