#ifndef GROUND_IPP_
#define GROUND_IPP_

#include "TEMLogger.h"

extern src::severity_logger<severity_level> glg;

/**
 * @brief Retrieves values of a specified member variable for each soil and rock layer.
 *
 * Iterates through the layers, extracting the specified variable for
 * valid soil and rock layers (isSoil/isRock && index below maximum
 * soil layer count).
 * Invalid layers retain a default-initialized value.
 *
 * @tparam T Data type of the member variable.
 * @param member Pointer to the Layer member variable to retrieve.
 * @param varname Variable name used for logging.
 * @return std::array<T, MAX_SOI_LAY> Array of by-layer values.
 */
template<typename T>
std::array<T, MAX_SOI_LAY> Ground::get_variable_bylayer(T Layer::*member, const std::string& varname) {

  BOOST_LOG_SEV(glg, debug) << "Getting by-layer " << varname;

  std::array<T, MAX_SOI_LAY> layer_array{};

  Layer* currl = fstsoill;
  int il = 0;

  while (currl != nullptr && il < MAX_SOI_LAY) {

      if (currl->isSoil || currl->isRock) {
          layer_array[il] = currl->*member;
      }

      currl = currl->nextl;
      il++;
  }

  return layer_array;
};

#endif /* GROUND_IPP_ */
