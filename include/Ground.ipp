#ifndef GROUND_IPP_
#define GROUND_IPP_

#include "TEMLogger.h"

extern src::severity_logger<severity_level> glg;

/**
 * @brief Retrieves values of a specified member variable for each soil and rock layer.
 *
 * Iterates through the layers, extracting the specified variable for
 * soil and rock layers. The values, type keys, and thicknesses at each
 * index describe the same layer. Only entries below count are valid;
 * unused entries retain default-initialized values.
 *
 * @tparam T Data type of the member variable.
 * @param member Pointer to the Layer member variable to retrieve.
 * @param varname Variable name used for logging.
 * @return Layer values, type keys, thicknesses in meters, and populated count.
 */
template<typename T>
LayerVariableProfile<T> Ground::get_variable_bylayer(
    T Layer::*member, const std::string& varname) const {

  BOOST_LOG_SEV(glg, debug) << "Getting by-layer " << varname;

  LayerVariableProfile<T> profile;

  const Layer* currl = fstsoill;

  while (currl != nullptr && profile.count < profile.values.size()) {
    if (currl->isSoil || currl->isRock) {
      const std::size_t il = profile.count;
      profile.values[il] = currl->*member;
      profile.tkey[il] = currl->tkey;
      profile.dz[il] = currl->dz;
      ++profile.count;
    }

    currl = currl->nextl;
  }

  return profile;
}

#endif /* GROUND_IPP_ */
