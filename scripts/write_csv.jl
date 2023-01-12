# Aiza 11/2022
# julia script containing the following functions:

# save_csv(paramkey,paramdist,initial_guess,problemname,obsweight): 
#   saves calibration setup + results to a csv file- problemname.csv

# get_itr_result(df,problemname): gets final results of calibration run, output in julia dataframe
#   df is a dataframe containing calibration setup, as follows:
#   df = DataFrame(parameters = paramkey,distribution = paramdist,weights = obsweight, initialGuess = initial_guess)
#   note - weights are optional

# save_model_csv(md,problemname,forward_predictions): 
#   saves observations and model results in a csv
#   if forward model hasn't been run, needs to be
#   This function requires Mads

import PyCall
using DataFrames
using CSV
using Pkg
using PyCall
Pkg.add("DataFrames")
Pkg.add("CSV")

function save_csv(paramkey,paramdist_min,paramdist_max,initial_guess,problemname,obsweight)
    if isempty(obsweight)
        df = DataFrame(parameters = paramkey,dist_min = paramdist_min, dist_max = paramdist_max, initialGuess = initial_guess)
    else
        df = DataFrame(parameters = paramkey,dist_min = paramdist_min, dist_max = paramdist_max, weights = obsweight, initialGuess = initial_guess)
    end
    df2=get_itr_results(problemname) 
    final_results=hcat(df,df2)
    if isfile(problemname*".csv")
        #if the problemname has already been used, we save a new file
        print(problemname*".csv already exists. Saving a new file: "*problemname*"_2.csv...")
        #append!(file,df)
        #print(file)
        CSV.write(problemname*"_2.csv", final_results)
    else
        CSV.write(problemname*".csv", final_results)
        print(problemname*".csv is saved.")
    end
end

function get_itr_results(problemname)
    #read in final results file
    pushfirst!(PyVector(pyimport("sys")."path"), @__DIR__)
    multi_cal = pyimport("process_multi_cal")
    lines=multi_cal.read_results(problemname*".finalresults");
    #extract out final param results
    merged_params=multi_cal.create_dict_params(lines);
    df2=permutedims(DataFrame(merged_params));
    # set OF error as column headers
    err=multi_cal.read_error(problemname*".finalresults");
    rename!(df2, err, makeunique=true)
    cols=size(df2,2)
    #if there are soil params, due to physical constraints, need to satisfy: Kdcraw > Kdcactive > Kdcpr > Kdccr
    if haskey(merged_params,"kdcrawc") 
        for nn in 1:cols
            if ~(df2[end-3,nn] > df2[end-2,nn] > df2[end-1,nn] > df2[end,nn])
                # assumes params are in this order at end: kdcrawc, kdcsoma, kdcsompr, kdcsomcr
                print("Calibration run "*nn*"does not meet soil parameters physical criteria. Removing results...")
                #discard results that don't meet criteria
                df2=select!(df2, Not(:nn))
            end
        end
    end
    return df2
end

# targets/obs are in md["Observations"].vals
# model data is forward_predictions.vals (vector) or forward_predictions (array) for random cals
# labels are Mads.gettargetkeys(md) or forward_predictions.keys
function save_model_csv(md,problemname,forward_predictions)
    m=(md["Observations"])
    keys=Mads.gettargetkeys(md)
    params=Mads.getparamkeys(md)
    x = Vector{Float64}()
    for o in keys
        t = Mads.gettarget(m[o])
        push!(x, t)
    end
    #for single calibration runs (Non random) we have not collected dict values into an array:
    if ~isa(forward_predictions,Array) 
        forward_predictions=collect(values(forward_predictions))
    end
    df = DataFrame(parameters = keys, observation = x, model = forward_predictions[:,1])
    cols=size(forward_predictions,2)
    if cols>1 
        for nn in 2:cols
            df2=DataFrame(model=forward_predictions[:,nn])
            df=hcat(df,df2,makeunique=true)
        end
    end
    CSV.write(problemname*"_model.csv", df)
    print(problemname*"_model.csv is saved.")
end