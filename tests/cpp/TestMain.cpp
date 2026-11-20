#include <gtest/gtest.h>

#include <cstdio>
#include <fstream>
#include <list>
#include <string>

#include "TEMUtilityFunctions.h"

namespace {

class ParameterFileParserTest : public testing::Test {
 protected:
  std::string fixture_path;

  void SetUp() override {
    fixture_path = std::string(testing::TempDir()) + "parameter-parser-test.txt";
  }

  void TearDown() override {
    std::remove(fixture_path.c_str());
  }

  void write_fixture(const std::string& contents) {
    std::ofstream fixture(fixture_path);
    ASSERT_TRUE(fixture.good());
    fixture << contents;
  }
};

TEST_F(ParameterFileParserTest, ReturnsOnlyTheRequestedCommunityTypeData) {
  write_fixture(
      "//===========================================================\n"
      "// CMT01 // Boreal Black Spruce // Murphy Dome\n"
      "      1.5  //rhq10://  //  //\n"
      "      2.5  //rhmoistfrozen://None//None//previously0.192\n"
      "//===========================================================\n"
      "// CMT02 // Tussock Tundra // Toolik\n"
      "      3.5  //rhq10://  //  //\n"
      "      4.5  //rhmoistfrozen://None//None//previously0.192\n");

  const std::list<std::string> values =
      temutil::parse_parameter_file(fixture_path, 2, 2);

  ASSERT_EQ(2, values.size());
  EXPECT_EQ("3.5", values.front());
  std::list<std::string>::const_iterator second_value = values.begin();
  ++second_value;
  EXPECT_EQ("4.5", *second_value);
}

TEST_F(ParameterFileParserTest, ParsesRealisticMultiPftRows) {
  write_fixture(
      "//===========================================================\n"
      "// CMT66 // Mature Jack Pine // BOREAS\n"
      "// EGreenTree   DecidShrub   Lichen   FeatherMoss   PFT4   PFT5   PFT6   PFT7   PFT8   PFT9\n"
      "  575.5300  122.8350  4.07800  32.4300  0.0000  0.0000  0.0000  0.0000  0.0000  0.0000 //cmax:0//  //  //\n"
      "    3.1000    2.5000  3.0000   4.480365  0.0000  0.0000  0.0000  0.0000  0.0000  0.0000 //nmax:0//  //  //\n"
      "//===========================================================\n"
      "// CMT67 // Mixed Forest // Groundhog River\n"
      "//DecidTrees   EGreenTree   Mosses   Forb   PFT4   PFT5   PFT6   PFT7   PFT8   PFT9\n"
      "  641.500000  305.100000  5.150000  12.570000  0.000000  0.000000  0.000000  0.000000  0.000000  0.000000 //cmax:501.8\n"
      "    9.500000    3.300000  4.200000   3.000000  0.000000  0.000000  0.000000  0.000000  0.000000  0.000000 //nmax:\n");

  std::list<std::string> values =
      temutil::parse_parameter_file(fixture_path, 67, 2);

  ASSERT_EQ(2, values.size());
  double cmax[NUM_PFT];
  temutil::pfll2data_pft(values, cmax);
  EXPECT_DOUBLE_EQ(641.5, cmax[0]);
  EXPECT_DOUBLE_EQ(12.57, cmax[3]);
  EXPECT_DOUBLE_EQ(0.0, cmax[9]);

  double nmax[NUM_PFT];
  temutil::pfll2data_pft(values, nmax);
  EXPECT_DOUBLE_EQ(9.5, nmax[0]);
  EXPECT_DOUBLE_EQ(3.0, nmax[3]);
  EXPECT_DOUBLE_EQ(0.0, nmax[9]);

}

TEST_F(ParameterFileParserTest, RejectsMissingCommunityTypeData) {
  write_fixture(
      "//===========================================================\n"
      "// CMT01 // Boreal Black Spruce // Murphy Dome\n"
      "1.5 //rhq10:\n");

  EXPECT_EXIT(
      { temutil::parse_parameter_file(fixture_path, 2, 3); },
      testing::ExitedWithCode(255),
      "");
}

TEST_F(ParameterFileParserTest, RejectsIncompleteCommunityTypeData) {
  write_fixture(
      "//===========================================================\n"
      "// CMT02 // Tussock Tundra // Toolik\n"
      "3.5 //rhq10:\n");

  EXPECT_EXIT(
      { temutil::parse_parameter_file(fixture_path, 2, 3); },
      testing::ExitedWithCode(255),
      "");
}

}  // namespace

int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
