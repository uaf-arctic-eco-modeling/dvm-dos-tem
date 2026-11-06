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
      "CMT01\n"
      "1.5\n"
      "2.5\n"
      "\n"
      "CMT02\n"
      "3.5\n"
      "4.5\n"
      "\n");

  const std::list<std::string> values =
      temutil::parse_parameter_file(fixture_path, 2, 3);

  ASSERT_EQ(3, values.size());
  EXPECT_EQ("CMT02", values.front());
  std::list<std::string>::const_iterator second_value = values.begin();
  ++second_value;
  EXPECT_EQ("3.5", *second_value);
  ++second_value;
  EXPECT_EQ("4.5", *second_value);
}

TEST_F(ParameterFileParserTest, RejectsMissingCommunityTypeData) {
  write_fixture(
      "CMT01\n"
      "1.5\n"
      "\n");

  EXPECT_EXIT(
      { temutil::parse_parameter_file(fixture_path, 2, 3); },
      testing::ExitedWithCode(255),
      "");
}

TEST_F(ParameterFileParserTest, RejectsIncompleteCommunityTypeData) {
  write_fixture(
      "CMT02\n"
      "3.5\n"
      "\n");

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
