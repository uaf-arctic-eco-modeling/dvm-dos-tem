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
using DataStructures
using CSV
using Pkg
using PyCall
Pkg.add("DataFrames")
Pkg.add("CSV")

function save_csv(paramkey,paramdist_min,paramdist_max,initial_guess,problemname,obsweight)
    if isempty(obsweight)
        df = DataFrame(parameters = paramkey,dist_min = paramdist_min, dist_max = paramdist_max, initialGuess = initial_guess)
    else
        if length(obsweight)<length(initial_guess)
            for nn in length(obsweight)+1:length(initial_guess)
                push!(obsweight, 0)
                nn=nn+1
            end
            df = DataFrame(parameters = paramkey,dist_min = paramdist_min, dist_max = paramdist_max, target_weights = obsweight, initialGuess = initial_guess)
        else
            df = DataFrame(parameters = paramkey,dist_min = paramdist_min, dist_max = paramdist_max, target_weights = obsweight, initialGuess = initial_guess)
        end
    end
    df2=get_itr_results(problemname,paramkey) 
    final_results=hcat(df,df2)
    # final_results=round.(final_results[:,Not(:parameters)], digits=2)
    CSV.write(problemname*".csv", final_results)
    print(problemname*".csv is saved.")
end

function get_itr_results(problemname,paramkey)
    #read in final results file
    pushfirst!(PyVector(pyimport("sys")."path"), @__DIR__)
    multi_cal = pyimport("process_multi_cal")
    lines=multi_cal.read_results(problemname*".finalresults");
    #extract out final param results
    merged_params=multi_cal.create_dict_params(lines);
    #Julia does not preserve order from python dict-use MADS paramkey to reorder julia dictionary correctly: 
    orderdict_idx = Dict(x => i for (i,x) in enumerate(paramkey)) #idx of correct order
    orderdict=OrderedDict([ name =>[] for name in paramkey])
    for nn in 1:length(orderdict)
        #find nn in vals of orderdict_idx, get associated key(param)
        idx=findall(item -> item == nn, orderdict_idx.vals) # idx is type: 1-element Vector{Int64}
        col_name = orderdict_idx.keys[idx[1]]
        #take column of assoc key in merged_params, add to ordered dict in correct spot
        orderdict[col_name]=merged_params[col_name]
    end
    df2=permutedims(DataFrame(orderdict));
    # set OF error as column headers
    err=multi_cal.read_error(problemname*".finalresults");
    rename!(df2, err, makeunique=true)
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
    df = DataFrame(obs_id = keys, observation = x, model = forward_predictions[:,1])
    cols=size(forward_predictions,2)
    if cols>1 
        for nn in 2:cols
            df2=DataFrame(model=forward_predictions[:,nn])
            df=hcat(df,df2,makeunique=true)
        end
    end
    df=round.(df[:,Not(:obs_id)], digits=5) #round values
    CSV.write(problemname*"_model.csv", df)
    print(problemname*"_model.csv is saved.")
end
