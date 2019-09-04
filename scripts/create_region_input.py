#!/usr/bin/env python

import sys

import subprocess

import shutil

import multiprocessing as mp

from contextlib import contextmanager

import configobj
import argparse
import textwrap
import os
import csv

import netCDF4

import datetime as dt
import numpy as np

import glob

'''
About the co2 data:

 - The "old" data are numbers that have been with dvmdostem for a long time and are
probably from here: https://www.esrl.noaa.gov/gmd/ccgg/trends/data.html

 - The RCP_85 ("new") data are from here: http://www.iiasa.ac.at/web-apps/tnt/RcpDb

Use this to snippet to plot them next to eachother.
    import pandas as pd
    import matplotlib.pyplot as plt
    odf = pd.DataFrame(dict(data=OLD_CO2_DATA, year=OLD_CO2_YEARS))
    ndf = pd.DataFrame(dict(data=RCP_85_CO2_DATA, year=RCP_85_CO2_YEARS))
    a = ndf.merge(odf, how='outer', on='year')
    plt.plot(a.year, a.data_x)
    plt.plot(a.year, a.data_y)
    plt.show()
'''
OLD_CO2_DATA = [ 296.311, 296.661, 297.04, 297.441, 297.86, 298.29, 298.726, 299.163,
  299.595, 300.016, 300.421, 300.804, 301.162, 301.501, 301.829, 302.154, 
  302.48, 302.808, 303.142, 303.482, 303.833, 304.195, 304.573, 304.966, 
  305.378, 305.806, 306.247, 306.698, 307.154, 307.614, 308.074, 308.531, 
  308.979, 309.401, 309.781, 310.107, 310.369, 310.559, 310.667, 310.697, 
  310.664, 310.594, 310.51, 310.438, 310.401, 310.41, 310.475, 310.605, 
  310.807, 311.077, 311.41, 311.802, 312.245, 312.736, 313.27, 313.842, 
  314.448, 315.084, 315.665, 316.535, 317.195, 317.885, 318.495, 318.935, 
  319.58, 320.895, 321.56, 322.34, 323.7, 324.835, 325.555, 326.55, 
  328.455, 329.215, 330.165, 331.215, 332.79, 334.44, 335.78, 337.655, 
  338.925, 340.065, 341.79, 343.33, 344.67, 346.075, 347.845, 350.055, 
  351.52, 352.785, 354.21, 355.225, 356.055, 357.55, 359.62, 361.69, 
  363.76, 365.83, 367.9, 368, 370.1, 372.2, 373.6943, 375.3507, 377.0071, 
  378.6636, 380.5236, 382.3536, 384.1336, 389.90, 391.65, 393.85, 396.52,
  398.65, 400.83, 404.24, 406.55 ]
OLD_CO2_YEARS = [ 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911,
  1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 
  1924, 1925, 1926, 1927, 1928, 1929, 1930, 1931, 1932, 1933, 1934, 1935, 
  1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 
  1948, 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
  1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 
  1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 
  1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 
  1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 
  2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017 ]

RCP_85_CO2_YEARS = [
1765,1766,1767,1768,1769,1770,1771,1772,1773,1774,1775,1776,1777,1778,1779,
1780,1781,1782,1783,1784,1785,1786,1787,1788,1789,1790,1791,1792,1793,1794,
1795,1796,1797,1798,1799,1800,1801,1802,1803,1804,1805,1806,1807,1808,1809,
1810,1811,1812,1813,1814,1815,1816,1817,1818,1819,1820,1821,1822,1823,1824,
1825,1826,1827,1828,1829,1830,1831,1832,1833,1834,1835,1836,1837,1838,1839,
1840,1841,1842,1843,1844,1845,1846,1847,1848,1849,1850,1851,1852,1853,1854,
1855,1856,1857,1858,1859,1860,1861,1862,1863,1864,1865,1866,1867,1868,1869,
1870,1871,1872,1873,1874,1875,1876,1877,1878,1879,1880,1881,1882,1883,1884,
1885,1886,1887,1888,1889,1890,1891,1892,1893,1894,1895,1896,1897,1898,1899,
1900,1901,1902,1903,1904,1905,1906,1907,1908,1909,1910,1911,1912,1913,1914,
1915,1916,1917,1918,1919,1920,1921,1922,1923,1924,1925,1926,1927,1928,1929,
1930,1931,1932,1933,1934,1935,1936,1937,1938,1939,1940,1941,1942,1943,1944,
1945,1946,1947,1948,1949,1950,1951,1952,1953,1954,1955,1956,1957,1958,1959,
1960,1961,1962,1963,1964,1965,1966,1967,1968,1969,1970,1971,1972,1973,1974,
1975,1976,1977,1978,1979,1980,1981,1982,1983,1984,1985,1986,1987,1988,1989,
1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001,2002,2003,2004,
2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,
2020,2021,2022,2023,2024,2025,2026,2027,2028,2029,2030,2031,2032,2033,2034,
2035,2036,2037,2038,2039,2040,2041,2042,2043,2044,2045,2046,2047,2048,2049,
2050,2051,2052,2053,2054,2055,2056,2057,2058,2059,2060,2061,2062,2063,2064,
2065,2066,2067,2068,2069,2070,2071,2072,2073,2074,2075,2076,2077,2078,2079,
2080,2081,2082,2083,2084,2085,2086,2087,2088,2089,2090,2091,2092,2093,2094,
2095,2096,2097,2098,2099,2100,2101,2102,2103,2104,2105,2106,2107,2108,2109,
2110,2111,2112,2113,2114,2115,2116,2117,2118,2119,2120,2121,2122,2123,2124,
2125,2126,2127,2128,2129,2130,2131,2132,2133,2134,2135,2136,2137,2138,2139,
2140,2141,2142,2143,2144,2145,2146,2147,2148,2149,2150,2151,2152,2153,2154,
2155,2156,2157,2158,2159,2160,2161,2162,2163,2164,2165,2166,2167,2168,2169,
2170,2171,2172,2173,2174,2175,2176,2177,2178,2179,2180,2181,2182,2183,2184,
2185,2186,2187,2188,2189,2190,2191,2192,2193,2194,2195,2196,2197,2198,2199,
2200,2201,2202,2203,2204,2205,2206,2207,2208,2209,2210,2211,2212,2213,2214,
2215,2216,2217,2218,2219,2220,2221,2222,2223,2224,2225,2226,2227,2228,2229,
2230,2231,2232,2233,2234,2235,2236,2237,2238,2239,2240,2241,2242,2243,2244,
2245,2246,2247,2248,2249,2250,2251,2252,2253,2254,2255,2256,2257,2258,2259,
2260,2261,2262,2263,2264,2265,2266,2267,2268,2269,2270,2271,2272,2273,2274,
2275,2276,2277,2278,2279,2280,2281,2282,2283,2284,2285,2286,2287,2288,2289,
2290,2291,2292,2293,2294,2295,2296,2297,2298,2299,2300,2301,2302,2303,2304,
2305,2306,2307,2308,2309,2310,2311,2312,2313,2314,2315,2316,2317,2318,2319,
2320,2321,2322,2323,2324,2325,2326,2327,2328,2329,2330,2331,2332,2333,2334,
2335,2336,2337,2338,2339,2340,2341,2342,2343,2344,2345,2346,2347,2348,2349,
2350,2351,2352,2353,2354,2355,2356,2357,2358,2359,2360,2361,2362,2363,2364,
2365,2366,2367,2368,2369,2370,2371,2372,2373,2374,2375,2376,2377,2378,2379,
2380,2381,2382,2383,2384,2385,2386,2387,2388,2389,2390,2391,2392,2393,2394,
2395,2396,2397,2398,2399,2400,2401,2402,2403,2404,2405,2406,2407,2408,2409,
2410,2411,2412,2413,2414,2415,2416,2417,2418,2419,2420,2421,2422,2423,2424,
2425,2426,2427,2428,2429,2430,2431,2432,2433,2434,2435,2436,2437,2438,2439,
2440,2441,2442,2443,2444,2445,2446,2447,2448,2449,2450,2451,2452,2453,2454,
2455,2456,2457,2458,2459,2460,2461,2462,2463,2464,2465,2466,2467,2468,2469,
2470,2471,2472,2473,2474,2475,2476,2477,2478,2479,2480,2481,2482,2483,2484,
2485,2486,2487,2488,2489,2490,2491,2492,2493,2494,2495,2496,2497,2498,2499,
2500]
RCP_85_CO2_DATA = [
 278.0516,  278.1062,  278.2204,  278.3431,  278.4706,  278.6005,  278.7328,  278.8688,
 279.0091,  279.1532,  279.3018,  279.4568,  279.6181,  279.7819,  279.9432,  280.0974,
 280.2428,  280.3817,  280.5183,  280.6572,  280.8026,  280.9568,  281.1181,  281.2819,
 281.4432,  281.5982,  281.7468,  281.8909,  282.0312,  282.1673,  282.2990,  282.4268,
 282.5509,  282.6712,  282.7873,  282.8990,  283.0068,  283.1109,  283.2113,  283.3074,
 283.3996,  283.4898,  283.5780,  283.6612,  283.7351,  283.7968,  283.8467,  283.8885,
 283.9261,  283.9627,  284.0011,  284.0427,  284.0861,  284.1285,  284.1667,  284.1982,
 284.2233,  284.2443,  284.2631,  284.2813,  284.3003,  284.3200,  284.3400,  284.3600,
 284.3800,  284.4000,  284.3850,  284.2800,  284.1250,  283.9750,  283.8250,  283.6750,
 283.5250,  283.4250,  283.4000,  283.4000,  283.4250,  283.5000,  283.6000,  283.7250,
 283.9000,  284.0750,  284.2250,  284.4000,  284.5750,  284.7250,  284.8750,  285.0000,
 285.1250,  285.2750,  285.4250,  285.5750,  285.7250,  285.9000,  286.0750,  286.2250,
 286.3750,  286.5000,  286.6250,  286.7750,  286.9000,  287.0000,  287.1000,  287.2250,
 287.3750,  287.5250,  287.7000,  287.9000,  288.1250,  288.4000,  288.7000,  289.0250,
 289.4000,  289.8000,  290.2250,  290.7000,  291.2000,  291.6750,  292.1250,  292.5750,
 292.9750,  293.3000,  293.5750,  293.8000,  294.0000,  294.1750,  294.3250,  294.4750,
 294.6000,  294.7000,  294.8000,  294.9000,  295.0250,  295.2250,  295.5000,  295.8000,
 296.1250,  296.4750,  296.8250,  297.2000,  297.6250,  298.0750,  298.5000,  298.9000,
 299.3000,  299.7000,  300.0750,  300.4250,  300.7750,  301.1000,  301.4000,  301.7250,
 302.0750,  302.4000,  302.7000,  303.0250,  303.4000,  303.7750,  304.1250,  304.5250,
 304.9750,  305.4000,  305.8250,  306.3000,  306.7750,  307.2250,  307.7000,  308.1750,
 308.6000,  309.0000,  309.4000,  309.7500,  310.0000,  310.1750,  310.3000,  310.3750,
 310.3750,  310.3000,  310.2000,  310.1250,  310.1000,  310.1250,  310.2000,  310.3250,
 310.5000,  310.7500,  311.1000,  311.5000,  311.9250,  312.4250,  313.0000,  313.6000,
 314.2250,  314.8475,  315.5000,  316.2725,  317.0750,  317.7950,  318.3975,  318.9250,
 319.6475,  320.6475,  321.6050,  322.6350,  323.9025,  324.9850,  325.8550,  327.1400,
 328.6775,  329.7425,  330.5850,  331.7475,  333.2725,  334.8475,  336.5250,  338.3600,
 339.7275,  340.7925,  342.1975,  343.7825,  345.2825,  346.7975,  348.6450,  350.7375,
 352.4875,  353.8550,  355.0175,  355.8850,  356.7775,  358.1275,  359.8375,  361.4625,
 363.1550,  365.3225,  367.3475,  368.8650,  370.4675,  372.5225,  374.7600,  376.8125,
 378.8125,  380.8275,  382.7775,  384.8000,  387.0123,  389.3242,  391.6380,  394.0087,
 396.4638,  399.0040,  401.6279,  404.3282,  407.0959,  409.9270,  412.8215,  415.7802,
 418.7963,  421.8644,  424.9947,  428.1973,  431.4747,  434.8262,  438.2446,  441.7208,
 445.2509,  448.8349,  452.4736,  456.1770,  459.9640,  463.8518,  467.8500,  471.9605,
 476.1824,  480.5080,  484.9272,  489.4355,  494.0324,  498.7297,  503.5296,  508.4327,
 513.4561,  518.6106,  523.9001,  529.3242,  534.8752,  540.5428,  546.3220,  552.2119,
 558.2122,  564.3131,  570.5167,  576.8434,  583.3047,  589.9054,  596.6466,  603.5205,
 610.5165,  617.6053,  624.7637,  631.9947,  639.2905,  646.6527,  654.0984,  661.6449,
 669.3047,  677.0776,  684.9543,  692.9020,  700.8942,  708.9316,  717.0155,  725.1360,
 733.3067,  741.5237,  749.8047,  758.1823,  766.6445,  775.1745,  783.7514,  792.3658,
 801.0188,  809.7146,  818.4221,  827.1572,  835.9559,  844.8047,  853.7254,  862.7260,
 871.7768,  880.8644,  889.9816,  899.1241,  908.2887,  917.4714,  926.6653,  935.8744,
 945.1321,  954.4662,  963.8391,  973.2408,  982.6804,  992.1429, 1001.6311, 1011.1191,
1020.6085, 1030.1004, 1039.5892, 1049.1233, 1058.7002, 1068.3216, 1077.9995, 1087.6999,
1097.4303, 1107.1765, 1116.9122, 1126.6592, 1136.4015, 1146.1344, 1155.9064, 1165.7401,
1175.6176, 1185.5295, 1195.4833, 1205.4772, 1215.4661, 1225.4530, 1235.4493, 1245.4190,
1255.3970, 1265.4211, 1275.4843, 1285.5943, 1295.7632, 1305.9625, 1316.1708, 1326.3936,
1336.6283, 1346.8594, 1357.0727, 1367.2797, 1377.5097, 1387.7930, 1398.1376, 1408.5226,
1418.9467, 1429.3969, 1439.8354, 1450.2111, 1460.4793, 1470.5915, 1480.5564, 1490.4552,
1500.2994, 1510.0573, 1519.7332, 1529.3276, 1538.8274, 1548.2214, 1557.5025, 1566.6838,
1575.7093, 1584.5792, 1593.3890, 1602.1444, 1610.8232, 1619.4189, 1627.9283, 1636.3423,
1644.6544, 1652.8621, 1660.9472, 1668.8714, 1676.6491, 1684.3479, 1691.9855, 1699.5543,
1707.0542, 1714.4671, 1721.7857, 1728.9986, 1736.0730, 1743.0204, 1749.8272, 1756.4845,
1763.0469, 1769.5420, 1775.9720, 1782.3281, 1788.5985, 1794.7605, 1800.7999, 1806.7334,
1812.5201, 1818.1423, 1823.6498, 1829.0556, 1834.3733, 1839.6122, 1844.7812, 1849.8682,
1854.8490, 1859.7106, 1864.4469, 1869.0362, 1873.4672, 1877.7840, 1881.9947, 1886.1097,
1890.1554, 1894.1313, 1898.0123, 1901.7766, 1905.4235, 1908.9603, 1912.3445, 1915.5465,
1918.6217, 1921.6126, 1924.5227, 1927.3520, 1930.1000, 1932.7513, 1935.2926, 1937.7127,
1940.0103, 1942.1583, 1944.1572, 1946.0278, 1947.7762, 1949.4392, 1951.0121, 1952.5138,
1953.9433, 1955.2718, 1956.4604, 1957.4929, 1958.4280, 1959.1897, 1959.7707, 1960.2847,
1960.7288, 1961.0674, 1961.3194, 1961.4957, 1961.5683, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774,
1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774, 1961.5774]

# for now, keep to a rectangular requirement?
# Select y,x or lat,lon bounding box coordinates for use?


# Data should be in a rectangular (grid) layout, NetCDF format.
# Should aim to conforms to CF & COARDS standards
# Geospatial information must be with the file. Each file should have 
# variables for Lat and Lon each defined in terms of the dimensions of (y,x) 
# where (y,x) are the rectangular grid coordinates.
#  --> Since extracting the Lat/Long info seems to be one of the slowest parts
#      of the process, and because keeping it in every file would result in 
#      a lot of redundant info, for now we are only storing spatial info
#      with the climate files.



def calc_pwin_str(x, y, xs=50, ys=50, poi_loc='lower-left'):
  if poi_loc != 'lower-left':
    print "ERROR! pixel of interest location selection only implemented for lower-left corner!"
    exit(-1)
  return [str(x), str(y+ys*1000), str(x+xs*1000), str(y)]
         #  ulx             uly             lrx     lry


def xform(lon, lat, in_srs='EPSG:4326', out_srs='EPSG:3338'):

  print "lon, lat, as input to xform(..):", lon, lat

  cmd = ['gdaltransform', '-s_srs', in_srs, '-t_srs', out_srs]
  p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  try:
    stdout, stderr = p.communicate("{} {}".format(lon, lat))
  except:
    p.kill()
    p.wait()
    raise

  if len(stderr) > 0:
    raise subprocess.CalledProcessError(stderr, cmd, output=stdout)
  else:
    x, y, h = stdout.split(' ')

  return float(x.strip()), float(y.strip()), float(h.strip())


def source_attr_string(ys='', xs='', yo='', xo='', msg=''):
  '''
  Returns a string to be included as a netCDF global attribute named "source".

  The string will start with the filename and function name responsible for
  creating the (new) input file, and if provided, will include values for size
  and offset. The size attributes are relatively self-explanatory (by looking
  at the size of the resulting file), and so can generally be ignored. The
  offset arguments are much more important to include.

  Parameters
  ----------
  ys, xs : str
    Strings denoting the spatial size of the domain.
  yo, xo : str
    Strings denoting the pixel offsets used by gdal_translate to create the
    input dataset.
  msg : str
    An additional message string to be included.

  Returns
  -------
  s : str
    A string something like:
    "./create_region_input.py::fill_veg_file --xoff 915 --yoff 292"
  '''
  import inspect
  cf = inspect.currentframe().f_back # <-- gotta look up one frame.

  # Start with the file name and function name
  s = "{}::{}".format(cf.f_code.co_filename, cf.f_code.co_name,)

  # add other info if present.
  for t, val in zip(['--xsize','--ysize','--xoff','--yoff',''],[xs,ys,xo,yo,msg]):
    if val != '':
      s += " {} {}".format(t, val)

  return s


def make_run_mask(filename, sizey=10, sizex=10, setpx='', match2veg=False, withlatlon=None, withproj=None, projwin=None):
  '''Generate a file representing the run mask'''

  if (withlatlon or withproj) and not match2veg:
    print "ERROR! If you want lat/lon or projection info in the run mask file you MUST specify 'match2veg=True'" 
    sys.exit(-1)

  print "Creating a run_mask file, %s by %s pixels." % (sizey, sizex)
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  run = ncfile.createVariable('run', np.int, ('Y', 'X',))

  spatial_decorate(ncfile, withlatlon=withlatlon, withproj=withproj)

  if setpx != '':
    y, x = setpx.split(",")
    print " --> NOTE: Turning off all pixels except (y,x): %s,%s." % (y, x)
    run[:] = np.zeros((sizey, sizex))
    run[y,x] = 1
    
  if match2veg:
    guess_vegfile = os.path.join(os.path.split(filename)[0], 'vegetation.nc')
    print "--> NOTE: Attempting to read: {:}".format(guess_vegfile)
    print "          and set runmask true where veg_class > 0."

    with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
      vd = vegFile.variables['veg_class'][:]

    run[:] = np.where(vd>0, 1, 0)

  ncfile.source = source_attr_string()
  ncfile.close()

  if withlatlon:
    with netCDF4.Dataset(filename, 'a') as dst:
      with netCDF4.Dataset(guess_vegfile, 'r') as src:
        dst.variables['lat'][:] = src.variables['lat'][:]
        dst.variables['lon'][:] = src.variables['lon'][:]

  if withproj:
    copy_grid_mapping(guess_vegfile, filename)
    with netCDF4.Dataset(filename, 'a') as dst:
      if get_gm_varname(dst):
        dst.variables['run'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))




def make_co2_file(filename, start_idx, end_idx, projected=False):
  '''Generates a co2 file for dvmdostem from the old sample data'''

  print "Creating a co2 file..."
  new_ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  # Dimensions
  yearD = new_ncfile.createDimension('year', None) # append along time axis
    
  # Coordinate Variable
  yearV = new_ncfile.createVariable('year', np.int, ('year',))
    
  # Data Variables
  co2 = new_ncfile.createVariable('co2', np.float32, ('year',))

  if not projected:
    print " --> NOTE: Hard-coding the values that were just ncdumped from the old file..."
    print " --> NOTE: Adding new values for 2010-2017. Using data from here:"
    print "           https://www.esrl.noaa.gov/gmd/ccgg/trends/data.html"
    print "           direct ftp link:"
    print "           ftp://aftp.cmdl.noaa.gov/products/trends/co2/co2_annmean_mlo.txt"
    new_ncfile.data_source = "https://www.esrl.noaa.gov/gmd/ccgg/trends/data.html"
    co2_data = OLD_CO2_DATA[start_idx:end_idx]
    co2_years = OLD_CO2_YEARS[start_idx:end_idx]
  else:
    print "--> NOTE: Using **projected** data from here: http://www.iiasa.ac.at/web-apps/tnt/RcpDb/dsd?Action=htmlpage&page=download"
    new_ncfile.data_source = "http://www.iiasa.ac.at/web-apps/tnt/RcpDb/dsd?Action=htmlpage&page=download"
    co2_data = RCP_85_CO2_DATA[start_idx:end_idx]
    co2_years = RCP_85_CO2_YEARS[start_idx:end_idx]

  co2[:] = co2_data
  yearV[:] = co2_years

  new_ncfile.source = source_attr_string()
  new_ncfile.close()


def create_template_topo_file(fname, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  '''Generate a template file for drainage classification.'''
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(fname, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  slope = ncfile.createVariable('slope', np.double, ('Y', 'X',))
  aspect = ncfile.createVariable('aspect', np.double, ('Y', 'X',))
  elevation = ncfile.createVariable('elevation', np.double, ('Y', 'X',))

  spatial_decorate(ncfile, withproj=withproj, withlatlon=withlatlon)

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_drainage_file(fname, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  '''Generate a template file for drainage classification.'''
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(fname, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  drainage_class = ncfile.createVariable('drainage_class', np.int, ('Y', 'X',))

  spatial_decorate(ncfile, withproj=withproj, withlatlon=withlatlon)

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_restart_nc_file(filename, sizex=10, sizey=10):
  '''Creates an empty restart file that can be used as a template?'''
  print "Creating an empty restart file: ", filename
  ncfile = netCDF4.Dataset(filename, mode='w', format='NETCDF4')

  print textwrap.dedent('''\
  %%%%%   NOTE   %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  Please note, this functionality may no longer be necessary, as functions have
  been added to the dvmdostem model that will allow it to create its own empty 
  restart files.
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  ''')

  # Dimensions for the file.
  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  pft        = ncfile.createDimension('pft', 10)
  pftpart    = ncfile.createDimension('pftpart', 3)
  snowlayer  = ncfile.createDimension('snowlayer', 6)
  rootlayer  = ncfile.createDimension('rootlayer', 10)
  soillayer  = ncfile.createDimension('soillayer', 23)
  rocklayer  = ncfile.createDimension('rocklayer', 5)
  fronts     = ncfile.createDimension('fronts', 10)
  prevten    = ncfile.createDimension('prevten', 10)
  prevtwelve = ncfile.createDimension('prevtwelve', 12)

  # Create variables...
  for v in ['dsr', 'numsnwl', 'numsl', 'rtfrozendays', 'rtunfrozendays', 'yrsdist']:
    ncfile.createVariable(v, np.int, ('Y', 'X'))

  for v in ['firea2sorgn', 'snwextramass', 'monthsfrozen', 'watertab', 'wdebrisc', 'wdebrisn', 'dmossc', 'dmossn']:
    ncfile.createVariable(v, np.double, ('Y', 'X'))

  for v in ['ifwoody', 'ifdeciwoody', 'ifperenial', 'nonvascular', 'vegage']:
    ncfile.createVariable(v, np.int, ('Y','X','pft'))

  for v in ['vegcov', 'lai', 'vegwater', 'vegsnow', 'labn', 'deadc', 'deadn', 'topt', 'eetmx', 'unnormleafmx', 'growingttime', 'foliagemx']:
    ncfile.createVariable(v, np.double, ('Y','X','pft'))

  for v in ['vegc', 'strn']:
    ncfile.createVariable(v, np.double, ('Y','X','pftpart', 'pft'))

  for v in ['TEXTUREsoil', 'FROZENsoil', 'TYPEsoil', 'AGEsoil',]:
    ncfile.createVariable(v, np.int, ('Y','X','soillayer'))

  for v in ['TSsoil', 'DZsoil', 'LIQsoil', 'ICEsoil', 'FROZENFRACsoil', 'rawc', 'soma', 'sompr', 'somcr', 'orgn', 'avln']:
    ncfile.createVariable(v, np.double, ('Y','X','soillayer'))

  for v in ['TSsnow', 'DZsnow', 'LIQsnow', 'RHOsnow', 'ICEsnow', 'AGEsnow']:
    ncfile.createVariable(v, np.double, ('Y','X','soillayer'))

  for v in ['TSrock', 'DZrock']:
    ncfile.createVariable(v, np.double, ('Y','X', 'rocklayer'))


  ncfile.createVariable('frontFT', np.int, ('Y','X', 'fronts'))
  ncfile.createVariable('frontZ', np.double, ('Y','X', 'fronts'))

  ncfile.createVariable('rootfrac', np.double, ('Y','X','rootlayer','pft'))

  for v in ['toptA','eetmxA','unnormleafmxA','growingttimeA']:
    ncfile.createVariable(v, np.double, ('Y','X','prevten','pft'))

  for v in ['prvltrfcnA']:
    ncfile.createVariable(v, np.double, ('Y','X','prevtwelve','pft'))

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_climate_nc_file(filename, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  '''Creates an empty climate file for dvmdostem; y,x grid, time unlimited.'''
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(filename, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(filename, mode="w", format='NETCDF4')

  # Dimensions for the file.
  time_dim = ncfile.createDimension('time', None) # append along time axis
  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Coordinate Variables
  Y = ncfile.createVariable('Y', np.int, ('Y',))
  X = ncfile.createVariable('X', np.int, ('X',))
  Y[:] = np.arange(0, sizey)
  X[:] = np.arange(0, sizex)

  spatial_decorate(ncfile, withlatlon=withlatlon, withproj=withproj)


  # Create data variables
  #co2 = ncfile.createVariable('co2', np.float32, ('time')) # actually year
  temp_air = ncfile.createVariable('tair', np.float32, ('time', 'Y', 'X',))
  precip = ncfile.createVariable('precip', np.float32, ('time', 'Y', 'X',))
  nirr = ncfile.createVariable('nirr', np.float32, ('time', 'Y', 'X',))
  vapor_press = ncfile.createVariable('vapor_press', np.float32, ('time', 'Y', 'X',))

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_fri_fire_file(fname, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(fname, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  # Do we need time dimension??

  spatial_decorate(ncfile, withlatlon=withlatlon, withproj=withproj)

  fri = ncfile.createVariable('fri', np.int32, ('Y','X',))
  sev = ncfile.createVariable('fri_severity', np.int32, ('Y','X'))
  dob = ncfile.createVariable('fri_jday_of_burn', np.int32, ('Y','X'))
  aob = ncfile.createVariable('fri_area_of_burn', np.int32, ('Y','X'))

  if rand:
    print "Fill FRI fire file with random data NOT IMPLEMENTED YET! See fill function."

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_explicit_fire_file(fname, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(fname, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)
  time = ncfile.createDimension('time', None)

  spatial_decorate(ncfile, withproj=withproj, withlatlon=withlatlon)

  exp_bm = ncfile.createVariable('exp_burn_mask', np.int32, ('time', 'Y', 'X',))
  exp_dob = ncfile.createVariable('exp_jday_of_burn', np.int32, ('time', 'Y', 'X',))
  exp_sev = ncfile.createVariable('exp_fire_severity', np.int32, ('time', 'Y','X'))
  exp_aob = ncfile.createVariable('exp_area_of_burn', np.int32, ('time', 'Y','X'))

  if rand:
    print "Fill EXPLICIT fire file with random data NOT IMPLEMENTED HERE! See fill function."

  ncfile.source = source_attr_string()
  ncfile.close()


def create_template_veg_nc_file(fname, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(fname, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  veg_class = ncfile.createVariable('veg_class', 'i4', ('Y', 'X',))

  spatial_decorate(ncfile, withlatlon=withlatlon, withproj=withproj)

  if (rand):
    print " --> NOTE: Filling with random data!"
    veg_class[:] = np.random.uniform(low=1, high=7, size=(sizey,sizex))

  ncfile.source = source_attr_string()
  ncfile.close()


def spatial_decorate(ncfile, withproj=None, withlatlon=None):
  '''
  Adds spatial variables to `ncfile`. 

  Assumes that `ncfile` is a valid netCDF dataset id, opened in append mode
  '''
  if withlatlon:
    lat = ncfile.createVariable('lat', np.float32, ('Y', 'X',))
    lon = ncfile.createVariable('lon', np.float32, ('Y', 'X',))

  if withproj:
    y = ncfile.createVariable('y', 'i4', ('Y'))
    x = ncfile.createVariable('x', 'i4', ('X'))

    y.standard_name = 'projection_y_coordinate'
    y.long_name = 'y coordinate of projection'
    y.units = 'm'

    x.standard_name = 'projection_x_coordinate'
    x.long_name = 'x coordinate of projection'
    x.units = 'm'

    ncfile.Conventions = "CF-1.5"  


def create_template_soil_texture_nc_file(fname, sizey=10, sizex=10, rand=None, withproj=None, withlatlon=None):
  print textwrap.dedent("""\
    Creating file: {}
        Shape: y:{} x:{}
        Fill with random data?: {}
        With projection?: {}
        With Lat/Lon?: {}""".format(fname, sizey, sizex, rand, withproj, withlatlon))

  ncfile = netCDF4.Dataset(fname, mode='w', format='NETCDF4')

  Y = ncfile.createDimension('Y', sizey)
  X = ncfile.createDimension('X', sizex)

  pct_sand = ncfile.createVariable('pct_sand', np.float32, ('Y','X'))
  pct_silt = ncfile.createVariable('pct_silt', np.float32, ('Y','X'))
  pct_clay = ncfile.createVariable('pct_clay', np.float32, ('Y','X'))

  spatial_decorate(ncfile, withproj=withproj, withlatlon=withlatlon)

  ncfile.source = source_attr_string()
  ncfile.close()


def convert_and_subset(in_file, master_output, xo, yo, xs, ys, yridx, midx, variablename, projwin):
  '''
  Convert a .tif to .nc file and subset it using pixel offsets.

  This is indended to be called as a independant multiprocessing.Process.

  Parameters
  ----------
  in_file : str (path)
    The tif file (from SNAP) with data in it
  master_output : str (path)
    The (per variable) master file that should get appended to.
  xo, yo : int
    The X and Y pixel offsets (lower left corner?)
  xs, ys : int
    The X and Y sizes (in pixels)
  yridx : int
    The year index for this in_file.
  midx : int
    The month index for this in_file
  variablename : str
    The variable we are working on. I.e. tair, precip, etc.

  Returns
  -------
  None
  '''
  cpn = mp.current_process().name

  tmpfile1 = os.path.join(os.path.dirname(master_output), 'tmp_script_{}'.format(variablename))
  tmpfile2 = os.path.join(os.path.dirname(master_output), 'tmp_script_{}_2.nc'.format(variablename))

  print "{:}: infile: {} master_output: {} vname: {}".format(
      cpn, in_file, master_output, variablename)

  print "{:}: Converting tif --> netcdf...".format(cpn)
  call_external_wrapper(['gdal_translate', '-of', 'netCDF', in_file, tmpfile1])

  if projwin:
    ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
    ex_call = ['gdal_translate', '-of', 'netCDF',
                 '-projwin', ulx, uly, lrx, lry,
                  tmpfile1, tmpfile2]
  else:
    ex_call = ['gdal_translate', '-of', 'netCDF',
                 '-srcwin', str(xo), str(yo), str(xs), str(ys),
                  tmpfile1, tmpfile2]

  print "{:}: Subsetting...".format(cpn)
  call_external_wrapper(ex_call)

  print "{:}: Writing subset's data to new file...".format(cpn)

  new_climatedataset = netCDF4.Dataset(master_output, mode='a')
  t2 = netCDF4.Dataset(tmpfile2, mode='r')

  theVariable = new_climatedataset.variables[variablename]
  theVariable[yridx*12+midx] = t2.variables['Band1'][:]

  new_climatedataset.close()
  t2.close()

  print "{:}: Done appending.".format(cpn)


def fill_topo_file(inSlope, inAspect, inElev, xo, yo, xs, ys, out_dir, of_name, withlatlon=None, withproj=None, projwin=None):
  '''Read subset of data from various tifs into single netcdf file for dvmdostem'''

  create_template_topo_file(of_name, sizey=ys, sizex=xs, withlatlon=True, withproj=True)

  # get a string for use as a file handle for each input file
  tmpSlope  = os.path.join(out_dir, 'tmp_cri_{}.nc'.format(os.path.splitext(os.path.basename(inSlope))[0]))
  tmpAspect = os.path.join(out_dir, 'tmp_cri_{}.nc'.format(os.path.splitext(os.path.basename(inAspect))[0]))
  tmpElev   = os.path.join(out_dir, 'tmp_cri_{}.nc'.format(os.path.splitext(os.path.basename(inElev))[0]))


  for inFile, tmpFile in zip([inSlope, inAspect, inElev], [tmpSlope, tmpAspect, tmpElev]):

    if projwin:
      ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
      ex_call = ['gdal_translate', '-of', 'netcdf',
                 '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
                 '-projwin', ulx, uly, lrx, lry,
                 inFile, tmpFile]
    else:
      ex_call = ['gdal_translate', '-of', 'netcdf',
                 '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
                 '-srcwin', str(xo), str(yo), str(xs), str(ys), 
                 inFile, tmpFile]

    subprocess.call(ex_call)

  with netCDF4.Dataset(of_name, mode='a') as new_topodataset:
    for ncvar, tmpFileName in zip(['slope','aspect','elevation'],[tmpSlope,tmpAspect,tmpElev]):
      with netCDF4.Dataset(tmpFileName, 'r') as TF:
        V = new_topodataset.variables[ncvar]
        V[:] = TF.variables['Band1'][:]

  if withlatlon:
    with netCDF4.Dataset(of_name, mode='a') as new_topodataset:
      with netCDF4.Dataset(tmpSlope, 'r') as TF:
        new_topodataset.variables['lat'][:] = TF.variables['lat'][:]
        new_topodataset.variables['lon'][:] = TF.variables['lon'][:]

  if withproj:

    copy_grid_mapping(tmpSlope, of_name)

    with netCDF4.Dataset(of_name, mode='a') as new_topodataset:
      for v in ['slope','aspect','elevation']:
        new_topodataset.variables[v].setncattr('grid_mapping', get_gm_varname(new_topodataset).encode('ascii'))

      with netCDF4.Dataset(tmpSlope, 'r') as TF:
        new_topodataset.variables['x'][:] = TF.variables['x'][:]
        new_topodataset.variables['y'][:] = TF.variables['y'][:]



def call_external_wrapper(call):
  '''
  Wrapper around subprocess.check_output that allows us to print stdout
  and stderr from the external command.
  '''
  print "Gearing up to call: ", call
  try:
    print "  --> stdout/stderr from external command:", subprocess.check_output(call, stderr=subprocess.STDOUT)
    success = True
  except subprocess.CalledProcessError as e:
    out = e.output.decode()
    success = False
    print "  --> ERROR! stdout/stderr from external command:", e.output.decode()

  if not success:
    sys.exit(-1)


def copy_grid_mapping(srcfile, dstfile):
  '''
  Takes paths to a source file and a destination file.
  This should deal with copying the spatial reference info from the input
  files into our new output files. This should allow our inputs to be more
  easily mapped. Maybe we don't need to carry the lat and lon variables thru if
  we have the grid_mapping???
  '''
  print "srcfile={}".format(srcfile)
  print "dstfile={}".format(dstfile)

  with netCDF4.Dataset(srcfile) as src, netCDF4.Dataset(dstfile, mode='a') as dst:

    if not any(['grid_mapping_name' in src.variables[v].ncattrs() for v in src.variables]):
      print "WARNING! Source file does not have grid mapping info!!"


    for v in src.variables:
      if 'grid_mapping_name' in src.variables[v].ncattrs():
        print "Creating variable...", v, " of type ", src.variables[v].datatype
        dst.createVariable(v, src.variables[v].datatype)

        # Setting en masse like this does not work, some attributes get
        # a string type specified (conversion from python unicode) which messes
        # up compatibility with downstream programs like gdal
        # https://github.com/Unidata/netcdf4-python/issues/529
        #dst[v].setncatts(src[v].__dict__)

        # So we set each attribute individually.
        for key, value in src[v].__dict__.iteritems():
          if type(value) != unicode:
            dst[v].setncattr(key, value)
          else:
            dst[v].setncattr(key, value.encode('ascii'))

      else:
        print "Passing on v=", v
        pass


def get_gm_varname(ds):
  '''Try to figure out which variable is the geo ref variable, return the name
  of the grid mapping, or None if the file appears to have no mapping.'''
  gm_var_name = None
  for vname, v in ds.variables.iteritems():
    if 'grid_mapping_name' in v.ncattrs():
      if vname != v.grid_mapping_name:
        print "ERROR!"
      else:
        gm_var_name = vname

  return gm_var_name


@contextmanager
def custom_netcdf_attr_bug_wrapper(ncid):
  # Maybe a bug? https://github.com/Unidata/netcdf4-python/issues/110
  ncid.setncattr('junkattr', 'somejunk')
  yield ncid
  del ncid.junkattr

def fill_veg_file(if_name, xo, yo, xs, ys, out_dir, of_name, withlatlon=None, withproj=None, projwin=None):
  '''Read subset of data from .tif into netcdf file for dvmdostem. '''

  # Create place for data
  create_template_veg_nc_file(of_name, sizey=ys, sizex=xs, rand=None, withlatlon=withlatlon, withproj=withproj)

  # Translate and subset to temporary location
  temporary = os.path.join(out_dir, 'tmp_cri_{}'.format(os.path.basename(of_name)))

  if not os.path.exists( os.path.dirname(temporary) ):
    os.makedirs(os.path.dirname(temporary))

  if projwin:
    ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
    ex_call = ['gdal_translate', '-of', 'netcdf',
     '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
     '-projwin', ulx, uly, lrx, lry,
     if_name, temporary]
  else:
    ex_call = ['gdal_translate', '-of', 'netcdf',
     '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
     '-srcwin', str(xo), str(yo), str(xs), str(ys),
     if_name, temporary]

  call_external_wrapper(ex_call)

  if withproj:
    copy_grid_mapping(temporary, of_name)

  # Copy from temporary location to into the placeholder file we just created
  with netCDF4.Dataset(temporary) as src, netCDF4.Dataset(of_name, mode='a') as new_vegdataset:

    veg_class = new_vegdataset.variables['veg_class']

    veg_class[:] = src.variables['Band1'][:].data

    with custom_netcdf_attr_bug_wrapper(new_vegdataset) as f:
      f.source = source_attr_string(xo=xo, yo=yo)

    if withlatlon:
      new_vegdataset.variables['lat'][:] = src.variables['lat'][:]
      new_vegdataset.variables['lon'][:] = src.variables['lon'][:]

    if withproj:
      if get_gm_varname(new_vegdataset):
        veg_class.setncattr('grid_mapping', get_gm_varname(new_vegdataset).encode('ascii'))
      new_vegdataset.variables['x'][:] = src.variables['x'][:]
      new_vegdataset.variables['y'][:] = src.variables['y'][:]

    # For some reason, some rows of the temporary file are numpy masked arrays
    # and if we don't directly access the data, then we get strange results '
    # (i.e. stuff that should be ocean shows up as CMT02??)
    # If we use the .data method, then the ocean ends up filled with '-1' and 
    # lakes end up as CMT00, which is what we want. Alternatively, could use the
    # .filled(-1) method.


def fill_climate_file(start_yr, yrs, xo, yo, xs, ys,
                      out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base,
                      time_coord_var, model='', scen='', cleanup_tmpfiles=True,
                      withlatlon=None, withproj=None, projwin=None):

  # create short handle for output file
  masterOutFile = os.path.join(out_dir, of_name)

  dataVarList = ['tair', 'precip', 'nirr', 'vapor_press']

  # Create empty file with all the correct dimensions. At the end data will
  # be copied into this file.
  create_template_climate_nc_file(masterOutFile, sizey=ys, sizex=xs, 
                                  withlatlon=withlatlon, withproj=withproj)

  # Start with setting up the spatial info (copying from input file)
  # Best do to this before the data so that we can catch bugs before waiting 
  # for all the data to copy.
  tmpfile =         os.path.join(out_dir, 'tmp_cri_file_with_spatial_info.nc'.format())
  smaller_tmpfile = os.path.join(out_dir, 'tmp_cri_file_with_spatial_info_smaller.nc'.format())

  print "Creating a temporary file with LAT and LON variables: ", tmpfile
  if type(sp_ref_file) == tuple:
    sp_ref_file = sp_ref_file[0]
  elif type(sp_ref_file) == str:
    pass # nothing to do...

  print "Convert from tif to netcdf..."
  call_external_wrapper(['gdal_translate', '-of', 'netCDF', 
      '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
      sp_ref_file, tmpfile])

  if projwin:
    ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
    ex_call = ['gdal_translate', '-of', 'netCDF',
        '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
        '-projwin', ulx, uly, lrx, lry,
        'NETCDF:"{}":Band1'.format(tmpfile), smaller_tmpfile]
  else:
    ex_call = ['gdal_translate', '-of', 'netCDF',
        '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
        '-srcwin', str(xo), str(yo), str(xs), str(ys),
        'NETCDF:"{}":Band1'.format(tmpfile), smaller_tmpfile]

  print "Subset (crop) netcdf file..."
  call_external_wrapper(ex_call)

  if withlatlon:
    print "Working on copying lat/lon info..."
    with netCDF4.Dataset(masterOutFile, mode='a') as dst:
      with netCDF4.Dataset(smaller_tmpfile, mode='r') as src:
        print "Copy the LAT/LON variables from the temporary file into our new dataset..."
        dst.variables['lat'][:] = src.variables['lat'][:]
        dst.variables['lon'][:] = src.variables['lon'][:]

        dst.variables['lat'].standard_name = 'latitude'
        dst.variables['lat'].units = 'degree_north'

        dst.variables['lon'].standard_name = 'longitude'
        dst.variables['lon'].units = 'degree_east'

    print "Done copying LON/LAT."

  print "Open new dataset for appending..."
  new_climatedataset = netCDF4.Dataset(masterOutFile, mode='a')

  # Write general attributes (applicable regardless of lat/lon or projection)
  with custom_netcdf_attr_bug_wrapper(new_climatedataset) as f:

    print "Write attribute with pixel offsets to file..."
    f.source = source_attr_string(xo=xo, yo=yo)

    print "Write attributes for model and scenario..."
    f.model = model
    f.scenario = scen

    print "Double check that we picked the right CF name for nirr!"
    f.variables['nirr'].standard_name = 'downwelling_shortwave_flux_in_air'
    f.variables['nirr'].units = 'W m-2'

    f.variables['precip'].standard_name = 'precipitation_amount'
    f.variables['precip'].units = 'mm month-1'

    f.variables['tair'].standard_name = 'air_temperature'
    f.variables['tair'].units = 'celsius'

    f.variables['vapor_press'].standard_name = 'water_vapor_pressure'
    f.variables['vapor_press'].units = 'hPa'

  print "Closing new dataset and temporary file."
  print "masterOutFile time dimension size: {}".format(new_climatedataset.dimensions['time'].size)
  new_climatedataset.close()


  # Copy the master into a separate file for each variable
  for v in dataVarList:
    shutil.copyfile(masterOutFile, os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)))

  # Now we have to loop over all the .tif files - there is one file for each
  # month of each year for each variable - and extract the data so we can
  # save it in our new NetCDF file.
  print "Working to prepare climate data for years %s to %s" % (start_yr, start_yr + yrs)
  for yridx, year in enumerate(range(start_yr, start_yr + yrs)):

    for midx, month in enumerate(range(1,13)): # Note 1 based month!

      print year, month

      basePathList = [in_tair_base, in_prec_base, in_rsds_base, in_vapo_base]
      baseFiles = [basePath + "{:02d}_{:04d}.tif".format(month, year) for basePath in basePathList]
      tmpFiles = [os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)) for v in dataVarList]
      procs = []
      for tiffimage, tmpFileName, vName in zip(baseFiles, tmpFiles , dataVarList):
        proc = mp.Process(target=convert_and_subset, args=(tiffimage, tmpFileName, xo, yo, xs, ys, yridx, midx, vName, projwin))
        procs.append(proc)
        proc.start()

      for proc in procs:
        proc.join()

  print "Done with year loop."

  with netCDF4.Dataset(masterOutFile, 'r') as ds:
    print "===> masterOutFile.dimensions: {}".format(ds.dimensions)

  print "Copy data from temporary per-variable files into master"
  tmpFiles = [os.path.join(out_dir, 'TEMP-{}-{}'.format(v, of_name)) for v in dataVarList]
  for tFile, var in zip(tmpFiles, dataVarList):
    # Need to make a list of variables to exclude from the
    # ncks append operation (all except the current variable)
    masked_list = [i for i in dataVarList if var not in i]

    opt_str = ("lat,lon," if withlatlon else "") + ",".join(masked_list)
    call_external_wrapper(['ncks', '--append', '-x','-v', opt_str, tFile, masterOutFile])
    os.remove(tFile)

    # This fails. Looks to me like a bug in nco as it expand the option string
    # import nco as NCO
    #nco = NCO.Nco()
    #opt_str = "--append -x -v lat,lon," + ",".join(masked_list)
    #nco.ncks(input=tFile, output=masterOutFile, options=opt_str)
    ''' Error from console:
    Copy data from temporary per-variable files into master /tmp/smaller-temporary-file-with-spatial-info.nc
    Error in calling operator ncks with:
    >>> /usr/local/bin/ncks - - a p p e n d - x - v p r e c i p , n i r r , v a p o r _ p r e s s --overwrite --output=some-dvmdostem-inputs/SouthBarrow_10x10/historic-climate.nc some-dvmdostem-inputs/SouthBarrow_10x10/TEMP-tair-historic-climate.nc <<<
    Inputs: some-dvmdostem-inputs/SouthBarrow_10x10/TEMP-tair-historic-climate.nc
    '''

  if withproj:
    # Super strange - this has to happen ***AFTER*** the ncks step or ncks complains 
    # about not being able to open the temporary file due to HDF Error...

    # Copy the grid mapping info
    copy_grid_mapping(smaller_tmpfile, masterOutFile)

    # set grid_mapping attribute on variables and copy y and x vars
    with netCDF4.Dataset(masterOutFile, mode='a') as dst:
      with netCDF4.Dataset(smaller_tmpfile, mode='r') as src:

        if get_gm_varname(dst):
          dst.variables['tair'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
          dst.variables['precip'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
          dst.variables['nirr'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
          dst.variables['vapor_press'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))

        dst.variables['x'][:] = src.variables['x'][:]
        dst.variables['y'][:] = src.variables['y'][:]

  if cleanup_tmpfiles:
    print "Cleaning up temporary files: {} and {}".format(tmpfile, smaller_tmpfile)
    os.remove(smaller_tmpfile)
    os.remove(tmpfile)

  with netCDF4.Dataset(masterOutFile, mode='a') as new_climatedataset:

    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    print "%% NOTE! Converting rsds (nirr) from MJ/m^2/day to W/m^2!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    nirr = new_climatedataset.variables['nirr']
    nirr[:] = (1000000 / (60*60*24)) * nirr[:]

    if time_coord_var:
      print "Write time coordinate variable attribute for time axis..."
      with custom_netcdf_attr_bug_wrapper(new_climatedataset) as f:
        tcV = f.createVariable("time", np.double, ('time'))
        tcV.setncatts({
          'long_name': 'time',
          'units': 'days since {}-1-1 0:0:0'.format(start_yr),
          'calendar': '365_day'
        })

        # Build up a vector of datetime stamps for the first day of each month
        try:
          num_months = f.dimensions['time'].size # only available in netCDF4 >1.2.2
        except AttributeError as e:
          num_months = len(f.dimensions['time'])

        # Gives an array of numpy datetime64 objects, which are monthly resolution
        assert start_yr+num_months/12 == start_yr+yrs, "Date/time indexing bug!"
        month_starts = np.arange('{}-01-01'.format(start_yr), '{}-01-01'.format(start_yr+yrs), dtype='datetime64[M]')

        print "length of month_starts array: {}".format(len(month_starts))

        # Using .tolist() to convert from numpy.datetime64 objects to python
        # standard library datetime.datetime objects only works for some 
        # of the available numpy.datetime units options! See here:
        # https://stackoverflow.com/questions/46921593#46921593
        assert month_starts[0].dtype == np.dtype('<M8[M]'), "Invalid type!"

        # Convert to python datetime.date objects
        month_starts_dateobjs = month_starts.tolist() 

        # Convert to python datetime.datetime objects with time set at 0
        month_starts_datetimeobjs = [dt.datetime.combine(i, dt.time()) for i in month_starts_dateobjs]
        print "length of month_starts_datetimeobjs: {}".format(len(month_starts_datetimeobjs))

        # Convert to numeric offset using netCDF utility function, the units,
        # and calendar.
        tcV_vals = netCDF4.date2num(month_starts_datetimeobjs, 
            units="days since {}-01-01".format(start_yr),
            calendar="365_day"
        )

        # Set the values for the time coordinate variable, using the
        # values from the helper function that computed the proper offsets
        tcV[:] = tcV_vals



def fill_soil_texture_file(if_sand_name, if_silt_name, if_clay_name, xo, yo, xs, ys, out_dir, of_name, 
      rand=True, withlatlon=None, withproj=None, projwin=None):
  
  create_template_soil_texture_nc_file(of_name, sizey=ys, sizex=xs, withlatlon=withlatlon, withproj=withproj)

  tmp_sand = os.path.join(out_dir, "tmp_cri_sand_tex.nc")
  tmp_silt = os.path.join(out_dir, "tmp_cri_silt_tex.nc")
  tmp_clay = os.path.join(out_dir, "tmp_cri_clay_tex.nc")

  if projwin:
    ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
    ex_call = ['gdal_translate','-of','netCDF',
               '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
               '-projwin', ulx, uly, lrx, lry]
  else:
    ex_call = ['gdal_translate','-of','netCDF',
               '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
               '-srcwin', str(xo), str(yo), str(xs), str(ys)]

  print "Subsetting TIF to netCDF"
  call_external_wrapper(ex_call + [if_sand_name, tmp_sand])

  call_external_wrapper(ex_call + [if_silt_name, tmp_silt])

  call_external_wrapper(ex_call + [if_clay_name, tmp_clay])


  if withproj:
    # arbitrarily pick one of the files to get the projection info from
    copy_grid_mapping(tmp_clay, of_name)

  with netCDF4.Dataset(of_name, mode='a') as dst:
    p_sand = dst.variables['pct_sand']
    p_silt = dst.variables['pct_silt']
    p_clay = dst.variables['pct_clay']
    
    if (rand):
      print "Filling file with random data."
      psand = np.random.uniform(low=0, high=100, size=(ys,xs))
      psilt = np.random.uniform(low=0, high=100, size=(ys,xs))
      pclay = np.random.uniform(low=0, high=100, size=(ys,xs))

      bigsum = psand + psilt + pclay

      p_sand[:] = np.round(psand/bigsum*100)
      p_silt[:] = np.round(psilt/bigsum*100)
      p_clay[:] = np.round(pclay/bigsum*100)

      print "WARNING: the random data is not perfect - due to rounding error, adding the percent sand/silt/clay does not always sum to exactly 100"

    else:
      print "Filling with real data..."

      print "Writing subset's data to new files..."
      with netCDF4.Dataset(tmp_sand, mode='r') as f:
        p_sand[:] = f.variables['Band1'][:]
      with netCDF4.Dataset(tmp_silt, mode='r') as f:
        p_silt[:] = f.variables['Band1'][:]
      with netCDF4.Dataset(tmp_clay, mode='r') as f:
        p_clay[:] = f.variables['Band1'][:]

    if withlatlon:
      # While we went to the trouble of writing lat/lon to all the temporary
      # files, we are only going to use one of those files to get the 
      # data into the final file...
      with netCDF4.Dataset(tmp_sand, mode='r') as src:
        dst.variables['lat'][:] = src.variables['lat'][:]
        dst.variables['lon'][:] = src.variables['lon'][:]

    if withproj:
      if get_gm_varname(dst):
        p_sand.setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
        p_silt.setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
        p_clay.setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))

      with netCDF4.Dataset(tmp_sand, mode='r') as src:
        dst.variables['x'][:] = src.variables['x'][:]
        dst.variables['y'][:] = src.variables['y'][:]

    with custom_netcdf_attr_bug_wrapper(dst) as f:
      f.source = source_attr_string(xo=xo, yo=yo)


def fill_drainage_file(if_name, xo, yo, xs, ys, out_dir, of_name, rand=False, withproj=None, withlatlon=None, projwin=None):

  create_template_drainage_file(of_name, sizey=ys, sizex=xs, withproj=withproj, withlatlon=withlatlon)

  tmpFile = os.path.join(out_dir, 'tmp_cri_drainage.nc')

  with netCDF4.Dataset(of_name, mode='a') as dst:

    '''Fill drainage template file'''
    if rand:
      print " --> NOTE: Filling with random data!"
      drain = dst.variables['drainage_class']
      drain[:] = np.random.randint(low=0, high=2, size=(ys, xs))

    else:
      print "Filling with real data"

      if projwin:
        ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
        ex_call = ['gdal_translate', '-of', 'netCDF',
                   '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
                   '-projwin', ulx, uly, lrx, lry,
                   if_name, tmpFile]
      else:
        ex_call = ['gdal_translate', '-of', 'netCDF',
                   '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
                   '-srcwin', str(xo), str(yo), str(xs), str(ys),
                   if_name, tmpFile]

      print "Subsetting TIF to netCDF..."
      call_external_wrapper(ex_call)

      with netCDF4.Dataset(tmpFile, mode='r') as src:
        drain = dst.variables['drainage_class']

        print "Thresholding: set data <= 200 to 0; set data > 200 to 1."
        data = src.variables['Band1'][:]
        data[data <= 200] = 0
        data[data > 200] = 1

        print "Writing subset data to new file"
        drain[:] = data

        if withlatlon:
          print "Writing lat/lon data to new file..."
          dst.variables['lat'][:] = src.variables['lat'][:]
          dst.variables['lon'][:] = src.variables['lon'][:]

    with custom_netcdf_attr_bug_wrapper(dst) as f:
      f.source = source_attr_string(xo=xo, yo=yo)



    if withproj:
      copy_grid_mapping(tmpFile, of_name)
  
      with netCDF4.Dataset(of_name, mode='a') as dst:

        if get_gm_varname(dst):
          dst.variables['drainage_class'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))

        with netCDF4.Dataset(tmpFile, mode='r') as src:
          dst.variables['x'][:] = src.variables['x'][:]
          dst.variables['y'][:] = src.variables['y'][:]




def fill_fri_fire_file(xo, yo, xs, ys, out_dir, of_name, datasrc='', if_name=None, withlatlon=None, withproj=None, projwin=None):
  '''
  Parameters:
  -----------
  datasrc : str describing how and where to get the numbers used to fill the file
    'random' will create files filled with random data
    'no-fires' will create files such that no fires occur
    'genet-greaves' will create files using H.Genet's and H.Greaves process   
  '''

  create_template_fri_fire_file(of_name, sizey=ys, sizex=xs, rand=False, withlatlon=withlatlon, withproj=withproj)

  guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
  print "--> NOTE: Attempting to read: {:} to get projection and or lat/lon info".format(guess_vegfile)

  if withproj:
    copy_grid_mapping(guess_vegfile, of_name)
    with netCDF4.Dataset(guess_vegfile ,'r') as src:
      with netCDF4.Dataset(of_name, mode='a') as dst:
        print "Writing projection x, y from veg file..."
        dst.variables['x'][:] = src.variables['x'][:]
        dst.variables['y'][:] = src.variables['y'][:]

        if get_gm_varname(dst):
          dst.variables['fri'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
          dst.variables['fri_severity'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
          dst.variables['fri_jday_of_burn'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
          dst.variables['fri_area_of_burn'].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))

  if withlatlon:
    with netCDF4.Dataset(guess_vegfile ,'r') as src:
      with netCDF4.Dataset(of_name, mode='a') as dst:
        print "Writing lat/lon from veg file..."
        dst.variables['lat'][:] = src.variables['lat'][:]
        dst.variables['lon'][:] = src.variables['lon'][:]

  if datasrc == 'random':
    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
    print "GENERATING FAKE DATA!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
    cmt2fireprops = {
      -1: {'fri':   -1, 'sev': -1, 'jdob':  -1, 'aob':  -1 }, # No data?
      0: {'fri':   -1, 'sev': -1, 'jdob':  -1, 'aob':  -1 }, # rock/snow/water
      1: {'fri':  100, 'sev':  3, 'jdob': 165, 'aob': 100 }, # black spruce
      2: {'fri':  105, 'sev':  2, 'jdob': 175, 'aob': 225 }, # white spruce
      3: {'fri':  400, 'sev':  3, 'jdob': 194, 'aob': 104 }, # boreal deciduous
      4: {'fri': 2000, 'sev':  2, 'jdob': 200, 'aob': 350 }, # shrub tundra
      5: {'fri': 2222, 'sev':  3, 'jdob': 187, 'aob': 210 }, # tussock tundra
      6: {'fri': 1500, 'sev':  1, 'jdob': 203, 'aob': 130 }, # wet sedge tundra
      7: {'fri': 1225, 'sev':  4, 'jdob': 174, 'aob': 250 }, # heath tundra
      8: {'fri':  759, 'sev':  3, 'jdob': 182, 'aob': 156 }, # maritime forest
    }
    guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
    print "--> NOTE: Attempting to read: {:} and set fire properties based on community type...".format(guess_vegfile)

    with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
      vd = vegFile.variables['veg_class'][:]
      fri = np.array([cmt2fireprops[i]['fri'] for i in vd.flatten()]).reshape(vd.shape)
      sev = np.array([cmt2fireprops[i]['sev'] for i in vd.flatten()]).reshape(vd.shape)
      jdob = np.array([cmt2fireprops[i]['jdob'] for i in vd.flatten()]).reshape(vd.shape)
      aob = np.array([cmt2fireprops[i]['aob'] for i in vd.flatten()]).reshape(vd.shape)

    with netCDF4.Dataset(of_name, mode='a') as nfd:
      print "==> write data to new FRI based fire file..."
      nfd.variables['fri'][:,:] = fri
      nfd.variables['fri_severity'][:,:] = sev
      nfd.variables['fri_jday_of_burn'][:,:] = jdob
      nfd.variables['fri_area_of_burn'][:,:] = aob

      with custom_netcdf_attr_bug_wrapper(nfd) as f:
        print "==> write global :source attribute to FRI fire file..."
        f.source = source_attr_string(xo=xo, yo=yo)


  elif datasrc == 'no-fires':
    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
    print "GENERATING FRI FILE WITH NO FIRES!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    with netCDF4.Dataset(of_name, mode='a') as nfd:
      print "==> write zeros to FRI file..."
      zeros = np.zeros((ys,xs))
      nfd.variables['fri'][:,:] = zeros
      nfd.variables['fri_severity'][:,:] = zeros
      nfd.variables['fri_jday_of_burn'][:,:] = zeros
      nfd.variables['fri_area_of_burn'][:,:] = zeros

      with custom_netcdf_attr_bug_wrapper(nfd) as f:
        print "==> write global :source attribute to FRI fire file..."
        f.source = source_attr_string(xo=xo, yo=yo)


  elif datasrc == 'fri-from-file': # other variables fixed/hardcoded below
    if not os.path.exists(if_name):
      print "ERROR! Can't find file specified for FRI input!: {}".format(if_name) 
      
    # Translate and subset to temporary location
    temporary = os.path.join(out_dir, 'tmp_cri_{}'.format(os.path.basename(of_name)))

    if not os.path.exists( os.path.dirname(temporary) ):
      os.makedirs(os.path.dirname(temporary))

    if projwin:
      ulx, uly, lrx, lry = calc_pwin_str(xo,yo,xs,ys)
      ex_call = ['gdal_translate', '-of', 'netcdf',
                 '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
                 '-projwin', ulx, uly, lrx, lry,
                 if_name, temporary]
    else:
      ex_call = ['gdal_translate', '-of', 'netcdf',
                 '-co', 'WRITE_LONLAT={}'.format('YES' if withlatlon else 'NO'),
                 '-srcwin', str(xo), str(yo), str(xs), str(ys),
                 if_name, temporary]

    subprocess.call(ex_call)

    with netCDF4.Dataset(temporary, mode='r') as temp_fri, netCDF4.Dataset(of_name, mode='a') as new_fri:
      print "--> Copying data from temporary subset file into new file..."
      new_fri.variables['fri'][:] = temp_fri.variables['Band1'][:]
      new_fri.variables['fri_severity'][:] = 2
      new_fri.variables['fri_jday_of_burn'][:] = 156
      new_fri.variables['fri_jday_of_burn'].setncatts({
          'long_name': 'julian day of burn'
        })
      new_fri.variables['fri_area_of_burn'][:] = 4.06283e+08 # square meters
      new_fri.variables['fri_area_of_burn'].setncatts({
          'long_name': 'area of burn',
          'units': 'm2',
          'note': "mean area of fire scar computed from statewide fire records 1950 to 1980"
        })

      with custom_netcdf_attr_bug_wrapper(new_fri) as f:
        print "==> write global :source attribute to FRI fire file..."
        f.source = source_attr_string(xo=xo, yo=yo)

  else:
    print "ERROR! Unrecognized value for 'datasrc' in function fill_fri_file(..)"



def fill_explicit_fire_file(yrs, xo, yo, xs, ys, out_dir, of_name, datasrc='', if_name=None, withlatlon=None, withproj=None, projwin=None):

  create_template_explicit_fire_file(of_name, sizey=ys, sizex=xs, rand=False, withlatlon=withlatlon, withproj=withproj)

  if datasrc =='no-fires':
    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%%%%%%%%%%%"
    print "GENERATING EXPLICIT FIRE FILE WITH NO FIRES!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    with netCDF4.Dataset(of_name, mode='a') as nfd:

        zeros = np.zeros((yrs,ys,xs))
        nfd.variables['exp_burn_mask'][:] = zeros
        nfd.variables['exp_jday_of_burn'][:] = zeros
        nfd.variables['exp_fire_severity'][:] = zeros
        nfd.variables['exp_area_of_burn'][:] = zeros

  elif datasrc == 'random':

    print "%%%%%%  WARNING  %%%%%%%%%%%%%%%%%"
    print "GENERATING FAKE DATA!"
    print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

    never_burn = ([9],[9])
    print "--> Never burn pixels: {}".format(zip(*never_burn))

    with netCDF4.Dataset(of_name, mode='a') as nfd:

      for yr in range(0, yrs):

        # Future: lookup from snap/alfresco .tif files...

        # Generate indices a few random pixels to burn
        flat_burn_indices = np.random.randint(0, (ys*xs), (ys*xs)*0.3)
        burn_indices = np.unravel_index(flat_burn_indices, (ys,xs))

        #print burn_indices
        # Now set the other variables, but only for the burning pixels...
        exp_bm = np.zeros((ys,xs))
        exp_jdob = np.zeros((ys,xs))
        exp_sev = np.zeros((ys,xs))
        exp_aob = np.zeros((ys,xs))

        exp_bm[burn_indices] = 1
        exp_jdob[burn_indices] = np.random.randint(152, 244, len(flat_burn_indices))
        exp_sev[burn_indices] = np.random.randint(0, 5, len(flat_burn_indices))
        exp_aob[burn_indices] = np.random.randint(1, 20000, len(flat_burn_indices))

        # Make sure far corner pixel never burns:
        exp_bm[never_burn] = 0

        nfd.variables['exp_burn_mask'][yr,:,:] = exp_bm
        nfd.variables['exp_jday_of_burn'][yr,:,:] = exp_jdob
        nfd.variables['exp_fire_severity'][yr,:,:] = exp_sev
        nfd.variables['exp_area_of_burn'][yr,:,:] = exp_aob

      print "Done filling out fire years..."

  else:
    print "ERROR! Unrecognized value for 'datasrc' in function fill_explicit_file(..)"

  # Now that the primary data is taken care of, fill out all some other general 
  # info for the file, lat, lon, attributes, etc

  def figure_out_time_size(of_name, yrs):
    guess_hcf = os.path.join(os.path.split(of_name)[0], 'historic-climate.nc')
    guess_pcf = os.path.join(os.path.split(of_name)[0], 'projected-climate.nc')

    starting_date_str = ''
    with netCDF4.Dataset(guess_hcf, 'r') as ds:
      if ds.variables['time'].size / 12 == yrs:
        starting_date_str = (ds.variables['time'].units).replace('days', 'years')
        end_date = netCDF4.num2date(ds.variables['time'][-1], ds.variables['time'].units, ds.variables['time'].calendar)

    with netCDF4.Dataset(guess_pcf, 'r') as ds:
      if ds.variables['time'].size / 12 == yrs:
        starting_date_str = (ds.variables['time'].units).replace('days', 'years')
        end_date = netCDF4.num2date(ds.variables['time'][-1], ds.variables['time'].units, ds.variables['time'].calendar)

    # Convert from the funky netcdf time object to python datetime object
    end_date = dt.datetime.strptime(end_date.strftime(), "%Y-%m-%d %H:%M:%S")

    return starting_date_str, end_date 

  # NOTE: For this to work you must run with --buildout-time-coord !!!
  guess_starting_date_string, end_date = figure_out_time_size(of_name, yrs)

  with netCDF4.Dataset(of_name, mode='a') as nfd:
    print "Write time coordinate variable attribute for time axis..."
    with custom_netcdf_attr_bug_wrapper(nfd) as f:
      tcV = f.createVariable("time", np.double, ('time'))
      start_date = dt.datetime.strptime('T'.join(guess_starting_date_string.split(' ')[-2:]), '%Y-%m-%dT%H:%M:%S')
      tcV[:] = np.arange( 0, (end_date.year+1 - start_date.year) )
      tcV.setncatts({
        'long_name': 'time',
        'units': '{}'.format(guess_starting_date_string),
        'calendar': '365_day'
      })


  guess_vegfile = os.path.join(os.path.split(of_name)[0], 'vegetation.nc')
  print "--> NOTE: Attempting to read: {:} to get lat/lon info".format(guess_vegfile)

  if withproj:
    copy_grid_mapping(guess_vegfile, of_name)
    with netCDF4.Dataset(of_name, mode='a') as dst:
      if get_gm_varname(dst):
        for v in ['exp_burn_mask','exp_jday_of_burn','exp_fire_severity','exp_area_of_burn']:
          dst.variables[v].setncattr('grid_mapping', get_gm_varname(dst).encode('ascii'))
      with netCDF4.Dataset(guess_vegfile, 'r') as src:
        dst.variables['x'][:] = src.variables['x'][:]
        dst.variables['y'][:] = src.variables['y'][:]

  if withlatlon:
    with netCDF4.Dataset(of_name, mode='a') as nfd:
      print "Writing lat/lon from veg file..."
      with netCDF4.Dataset(guess_vegfile ,'r') as vegFile:
        nfd.variables['lat'][:] = vegFile.variables['lat'][:]
        nfd.variables['lon'][:] = vegFile.variables['lon'][:]


  print "Setting :source attribute on new explicit fire file..."
  with netCDF4.Dataset(of_name, mode='a') as dst:
    with custom_netcdf_attr_bug_wrapper(dst) as ds:
      ds.source = source_attr_string(xo=xo, yo=yo)



def verify_paths_in_config_dict(tif_dir, config):

  def pretty_print_test_path(test_path, k):
    if os.path.exists(test_path):
      print "key {} is OK!".format(k)
    else:
      print "ERROR! Can't find config path!! key:{} test_path: {}".format(k, test_path)

  for k, v in config.iteritems():

    if 'src' in k:

      if 'soil' in k:
        required_for = ['soil']
      if 'drainage' in k:
        required_for = ['drainage']
      if 'top' in k:
        required_for = ['topo']
      if 'veg' in k:
        required_for = ['vegetation']

      # Check the climate stuff
      if 'clim' in k:
        if 'h clim' in k:
          required_for = ['historic-climate']
          fy = config['h clim first yr']
        elif 'p clim' in k:
          required_for = ['projected-climate']
          fy = config['p clim first yr']
        else:
          pass #??

        test_path = os.path.join(tif_dir,"{}01_{}.tif".format(v, fy))
        pretty_print_test_path(test_path, k)

      # Check the fire stuff
      elif 'fire fri' in k:
        test_path = os.path.join(tif_dir, v)
        pretty_print_test_path(test_path, k)

      # Check all the other src files...
      else:
        test_path = os.path.join(tif_dir, v)
        pretty_print_test_path(test_path, k)


def main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir, 
         files=[], config={}, time_coord_var=False,
         clip_projected2match_historic=False,
         withlatlon=None, withproj=None, projwin=False, cleanup=False):

  #
  # Make the veg file first, then run-mask, then climate, then fire.
  #
  # The fire files require the presence of the veg map, and climate!
  #
  if 'vegetation' in files:
    of_name = os.path.join(out_dir, "vegetation.nc")
    #fill_veg_file(os.path.join(tif_dir,  "ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif"), xo, yo, xs, ys, out_dir, of_name)
    fill_veg_file(os.path.join(tif_dir, config['veg src']), xo, yo, xs, ys, out_dir, of_name, withlatlon=withlatlon, withproj=withproj, projwin=projwin)

  if 'drainage' in files:
    of_name = os.path.join(out_dir, "drainage.nc")
    fill_drainage_file(os.path.join(tif_dir,  config['drainage src']), xo, yo, xs, ys, out_dir, of_name, withlatlon=withlatlon, withproj=withproj, projwin=projwin)

  if 'soil-texture' in files:
    of_name = os.path.join(out_dir, "soil-texture.nc")

    in_clay_base = os.path.join(tif_dir, config['soil clay src'])
    in_sand_base = os.path.join(tif_dir, config['soil sand src'])
    in_silt_base = os.path.join(tif_dir, config['soil silt src'])

    fill_soil_texture_file(in_sand_base, in_silt_base, in_clay_base, xo, yo, xs, ys, out_dir, of_name, rand=False, withlatlon=withlatlon, withproj=withproj, projwin=projwin)

  if 'topo' in files:
    of_name = os.path.join(out_dir, "topo.nc")

    in_slope = os.path.join(tif_dir, config['topo slope src'])
    in_aspect = os.path.join(tif_dir, config['topo aspect src'])
    in_elev = os.path.join(tif_dir, config['topo elev src'])

    fill_topo_file(in_slope, in_aspect, in_elev, xo,yo,xs,ys,out_dir, of_name, withlatlon=withlatlon, withproj=withproj, projwin=projwin)

  if 'run-mask' in files:
    make_run_mask(os.path.join(out_dir, "run-mask.nc"), sizey=ys, sizex=xs, match2veg=True, withlatlon=withlatlon, withproj=withproj, projwin=projwin) #setpx='1,1')

  if 'co2' in files:
    sidx = OLD_CO2_YEARS.index(int(config['h clim first yr']))
    eidx = OLD_CO2_YEARS.index(int(config['h clim last yr']))+1
    make_co2_file(os.path.join(out_dir, "co2.nc"), sidx, eidx, projected=False)

  if 'projected-co2' in files:
    sidx = RCP_85_CO2_YEARS.index(int(config['p clim first yr']))
    eidx = RCP_85_CO2_YEARS.index(int(config['p clim last yr'])) + 1
    #eidx = None # Take it all!!
    if 'co2' in files and 'projected-co2' in files:
      if clip_projected2match_historic:
        sidx = RCP_85_CO2_YEARS.index(int(config['h clim last yr'])) + 1
        eidx = RCP_85_CO2_YEARS.index(int(config['p clim last yr'])) + 1

    make_co2_file(os.path.join(out_dir, "projected-co2.nc"), sidx, eidx, projected=True)

  if 'historic-climate' in files:
    of_name = "historic-climate.nc"
    # Tried parsing this stuff automatically from the above paths,
    # but the paths, names, directory structures, etc were not standardized
    # enough to be worth it.
    first_avail_year    = int(config['h clim first yr'])
    last_avail_year     = int(config['h clim last yr'])
    origin_institute    = config['h clim orig inst']
    version             = config['h clim ver']
    in_tair_base = os.path.join(tif_dir, config['h clim tair src'])
    in_prec_base = os.path.join(tif_dir, config['h clim prec src'])
    in_rsds_base = os.path.join(tif_dir, config['h clim rsds src'])
    in_vapo_base = os.path.join(tif_dir, config['h clim vapo src'])

    # Use the the January file for the first year requested as a spatial reference
    sp_ref_file  = "{}{month:02d}_{starty:04d}.tif".format(in_tair_base, month=1, starty=first_avail_year),

    # Calculates number of years for running all. Values are different
    # for historic versus projected.
    hc_years = 0
    if years == -1:
      filecount = len(glob.glob(in_tair_base + "*.tif"))
      print "Found %s files..." % filecount
      hc_years = (filecount/12) - start_year
    else:
      hc_years = years

    #print "filecount: {}".format(filecount)
    print "hc_years: {}".format(hc_years)
    fill_climate_file(first_avail_year+start_year, hc_years,
                      xo, yo, xs, ys,
                      out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base,
                      time_coord_var, model=origin_institute, scen=version, 
                      withlatlon=withlatlon, withproj=withproj,
                      cleanup_tmpfiles=cleanup, projwin=projwin)


  if 'projected-climate' in files:
    of_name = "projected-climate.nc"

    # Tried parsing this stuff automatically from the above paths,
    # but the paths, names, directory structures, etc were not standardized
    # enough to be worth it.
    first_avail_year    = int(config['p clim first yr'])
    last_avail_year     = int(config['p clim last yr'])
    origin_institute    = config['p clim orig inst']
    version             = config['p clim ver']
    in_tair_base = os.path.join(tif_dir, config['p clim tair src'])
    in_prec_base = os.path.join(tif_dir, config['p clim prec src'])
    in_rsds_base = os.path.join(tif_dir, config['p clim rsds src'])
    in_vapo_base = os.path.join(tif_dir, config['p clim vapo src'])

    # Pick the starting year of the projected file to immediately follow the 
    # last year in the historic file.
    if ('projected-climate' in files) and ('historic-climate' in files):
      if clip_projected2match_historic:

        # Look up the last year that is in the historic data
        # assumes that the historic file was just created, and so exists and 
        # is reliable...
        with netCDF4.Dataset(os.path.join(out_dir, 'historic-climate.nc'), 'r') as hds:
          end_hist = netCDF4.num2date(hds.variables['time'][-1], hds.variables['time'].units, calendar=hds.variables['time'].calendar)
        print "The historic dataset ends at {}".format(end_hist)

        if (first_avail_year > end_hist.year+1):
          print """==> WARNING! There will be a gap between the historic and 
          projected climate files!! Ignoring --start-year offset and will 
          start building at the beginning of the projected period ({})
          """.format(first_avail_year)
          start_year = 0
        else:
          # Override start_year
          start_year = (end_hist.year - first_avail_year) + 1 
          print """Setting start year for projected data to be immediately 
          following the historic data. 
          End historic: {} 
          Beginning projected: {}
          start_year offset: {}""".format(end_hist.year, first_avail_year + start_year, start_year)

    # Set the spatial reference file. Use the first month of the starting year
    sp_ref_file  = "{}{month:02d}_{starty:04d}.tif".format(in_tair_base, month=1, starty=first_avail_year),

    # Calculates number of years for running all. Values are different
    # for historic versus projected.
    pc_years = 0;
    if years == -1:
      filecount = len(glob.glob(in_tair_base + "*.tif"))
      print "Found %s files..." % filecount
      pc_years = (filecount/12) - start_year
    else:
      pc_years = years

    #print "filecount: {}".format(filecount)
    print "pc_years: {}".format(pc_years)
    fill_climate_file(first_avail_year + start_year, pc_years,
                      xo, yo, xs, ys, out_dir, of_name, sp_ref_file,
                      in_tair_base, in_prec_base, in_rsds_base, in_vapo_base,
                      time_coord_var, model=origin_institute, scen=version,
                      withlatlon=withlatlon, withproj=withproj,
                      cleanup_tmpfiles=cleanup, projwin=projwin)


  # Conform CO2 to climate!!
  if all([f in files for f in 'historic-climate','projected-climate','co2','projected-co2']):
    pass

  if 'fri-fire' in files:
    of_name = os.path.join(out_dir, "fri-fire.nc")
    fill_fri_fire_file(
        xo, yo, xs, ys, out_dir, of_name, 
        datasrc='no-fires', 
        if_name=None,
        withlatlon=withlatlon, withproj=withproj, projwin=projwin
    )

  if 'historic-explicit-fire' in files:
    of_name = os.path.join(out_dir, "historic-explicit-fire.nc")

    climate = os.path.join(os.path.split(of_name)[0], 'historic-climate.nc')
    print "--> NOTE: Guessing length of time dimension from: {:}".format(climate)
    with netCDF4.Dataset(climate, 'r') as climate_dataset:
      years = len(climate_dataset.dimensions['time']) / 12

    fill_explicit_fire_file(
        years, xo, yo, xs, ys, out_dir, of_name,
        datasrc='no-fires',
        if_name=None, withlatlon=withlatlon, withproj=withproj, projwin=projwin
    )

  if 'projected-explicit-fire' in files:
    of_name = os.path.join(out_dir, "projected-explicit-fire.nc")

    climate = os.path.join(os.path.split(of_name)[0], 'projected-climate.nc')
    print "--> NOTE: Guessing length of time dimension from: {:}".format(climate)
    with netCDF4.Dataset(climate, 'r') as climate_dataset:
      years = len(climate_dataset.dimensions['time']) / 12

    fill_explicit_fire_file(
        years, xo, yo, xs, ys, out_dir, of_name,
        datasrc='no-fires',
        if_name=None, withlatlon=withlatlon, withproj=withproj, projwin=projwin
    )

  if cleanup:
    tmp_files = glob.glob(os.path.join(out_dir, "tmp_*"))
    print "Found {} temporary files in {}".format(len(tmp_files), out_dir)
    for f in tmp_files:
      print "Removing ", f
      os.remove(f)



  print(textwrap.dedent('''\

      ----> CAVEATS:
       * The input file series are from SNAP, use CRU-TS40 for historic climate
         and AR5 for the projected climate.
  '''))

  print "DONE"



def get_slurm_wrapper_string(tifs, pclim='ncar-ccsm4', 
    sitename='TOOLIK_FIELD_STATION', yoff=68.62854, xoff=-149.517149, 
    xsize=10, ysize=10, coordtype="--lonlat \\"):
  '''
  When running this program (create_region_input.py) on atlas, it is best to
  run under the control of the queue manager (slurm). This function is a place
  to store a wrapper script that can be submitted to slurm.

  Returns string with text for slurm script. The wrapper script has named
  template parameters that correspond to the named kwargs for this function.

  The two backslashes (e.g for coordtype) are necessary for escaping optional
  parameters in the command line passed to slurm's srun command.
  '''
  
  slurm_wrapper = textwrap.dedent('''\
    #!/bin/bash

    #SBATCH --cpus-per-task=4
    #SBATCH --ntasks=1
    #SBATCH -p main

    # Offsets for new ar5/rcp85 datasets found in:
    TIFDIR="{tifs}"
    PCLIM="{pclim}"
    NAME="{sitename}"

    site=cru-ts40_ar5_rcp85_"$PCLIM"_"$NAME"
    xoff={xoff}; yoff={yoff}
    XSIZE={xsize}; YSIZE={ysize}

    srun ./scripts/create_region_input.py \\
      --tifs $TIFDIR \\
      --tag $site \\
      --years -1 \\
      --buildout-time-coord \\
      {coordtype}
      --yoff $yoff --xoff $xoff --xsize $XSIZE --ysize $YSIZE \\
      --which all \\
      --projected-climate-config "$PCLIM" \\
      --clip-projected2match-historic \\
      --withlatlon \\
      --withproj \\
      --cleanup

    # Add an output directory, some downstream processes assume it exists.
    mkdir -p input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/output

    # Handle auxiliary steps, e.g. cropping, gapfilling, plotting

    # Generate plots for double checking data... (Should this be submitted with srun too??)
    #./scripts/input_util.py climate-ts-plot --type annual-summary --yx 0 0 input-staging-area/

    # REMEMBER TO CHECK FOR GAPFILLING NEEDS!!!
    srun ./scripts/gapfill.py --dry-run --input-folder input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/

    # Run script to swap all CMT 8 pixels to CMT 7
    srun ./scripts/fix_vegetation_file_cmt08_to_cmt07.py input-staging-area/"$site"_"$YSIZE"x"$XSIZE"/vegetation.nc
    '''.format(tifs=tifs, pclim=pclim, sitename=sitename, xoff=xoff, yoff=yoff, 
        xsize=xsize, ysize=ysize, coordtype=coordtype))

  return slurm_wrapper



  '''
  Returns a configuration object with all the required keys, but no values.
  '''
  empty_config_string = textwrap.dedent('''\
      veg src = ''

      drainage src = ''

      soil clay src = ''
      soil sand src = ''
      soil silt src = ''

      topo slope src = ''
      topo aspect src = ''
      topo elev src = ''

      h clim first yr = ''
      h clim last yr = ''
      h clim orig inst = ''
      h clim ver = ''
      h clim tair src = ''
      h clim prec src = ''
      h clim rsds src = ''
      h clim vapo src = ''

      p clim first yr = ''
      p clim last yr = ''
      p clim ver = ''
      p clim orig inst = ''
      p clim tair src = ''
      p clim prec src = ''
      p clim rsds src = ''
      p clim vapo src = ''

      fire fri src = ''
    ''')
  return configobj.ConfigObj(empty_config_string.split("\n"))




if __name__ == '__main__':

  base_ar5_rcp85_config = textwrap.dedent('''\
    veg src = 'ancillary/land_cover/v_0_4/iem_vegetation_model_input_v0_4.tif'

    drainage src = 'ancillary/drainage/Lowland_1km.tif'

    soil clay src = 'ancillary/BLISS_IEM/mu_claytotal_r_pct_0_25mineral_2_AK_CAN.img'
    soil sand src = 'ancillary/BLISS_IEM/mu_sandtotal_r_pct_0_25mineral_2_AK_CAN.img'
    soil silt src = 'ancillary/BLISS_IEM/mu_silttotal_r_pct_0_25mineral_2_AK_CAN.img'

    topo slope src = 'ancillary/slope/iem_prism_slope_1km.tif'
    topo aspect src = 'ancillary/aspect/iem_prism_aspect_1km.tif'
    topo elev src = 'ancillary/elevation/iem_prism_dem_1km.tif'

    h clim first yr = 1901
    h clim last yr = 2015
    h clim orig inst = 'CRU'
    h clim ver = 'TS40'
    h clim tair src = 'tas_mean_C_iem_cru_TS40_1901_2015/tas/tas_mean_C_CRU_TS40_historical_'
    h clim prec src = 'pr_total_mm_iem_cru_TS40_1901_2015/pr_total_mm_CRU_TS40_historical_'
    h clim rsds src = 'rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_1901_2015_fix/rsds/rsds_mean_MJ-m2-d1_iem_CRU-TS40_historical_'
    h clim vapo src = 'vap_mean_hPa_iem_CRU-TS40_historical_1901_2015_fix/vap/vap_mean_hPa_iem_CRU-TS40_historical_'

    fire fri src = 'iem_ancillary_data/Fire/FRI.tif'
  ''')

  mri_cgcm3_ar5_rcp85_config = textwrap.dedent('''\
    p clim first yr = 2006
    p clim last yr = 2100
    p clim ver = 'rcp85'

    p clim orig inst = 'MRI-CGCM3'
    p clim tair src = 'tas_mean_C_ar5_MRI-CGCM3_rcp85_2006_2100/tas/tas_mean_C_iem_ar5_MRI-CGCM3_rcp85_'
    p clim prec src = 'pr_total_mm_ar5_MRI-CGCM3_rcp85_2006_2100/pr/pr_total_mm_iem_ar5_MRI-CGCM3_rcp85_'
    p clim rsds src = 'rsds_mean_MJ-m2-d1_ar5_MRI-CGCM3_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_MRI-CGCM3_rcp85_'
    p clim vapo src = 'vap_mean_hPa_ar5_MRI-CGCM3_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_MRI-CGCM3_rcp85_'
  ''')

  ncar_ccsm4_ar5_rcp85_config = textwrap.dedent('''\
    p clim first yr = 2006
    p clim last yr = 2100
    p clim ver = 'rcp85'

    p clim orig inst = 'NCAR-CCSM4'
    p clim tair src = 'tas_mean_C_ar5_NCAR-CCSM4_rcp85_2006_2100/tas/tas_mean_C_iem_ar5_NCAR-CCSM4_rcp85_'
    p clim prec src = 'pr_total_mm_ar5_NCAR-CCSM4_rcp85_2006_2100/pr/pr_total_mm_iem_ar5_NCAR-CCSM4_rcp85_'
    p clim rsds src = 'rsds_mean_MJ-m2-d1_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/rsds/rsds_mean_MJ-m2-d1_iem_ar5_NCAR-CCSM4_rcp85_'
    p clim vapo src = 'vap_mean_hPa_ar5_NCAR-CCSM4_rcp85_2006_2100_fix/vap/vap_mean_hPa_iem_ar5_NCAR-CCSM4_rcp85_'
  ''')



  fileChoices = ['run-mask', 'co2', 'projected-co2', 'vegetation', 'drainage', 'soil-texture', 'topo',
                 'fri-fire', 'historic-explicit-fire', 'projected-explicit-fire',
                 'historic-climate', 'projected-climate']

  # maintain subsets of the file choices to ease argument combo verification  
  temporal_file_choices = [
    #'co2', 'projected-co2',
    'historic-explicit-fire','projected-explicit-fire',
    'historic-climate','projected-climate'
  ]
  spatial_file_choices = [f for f in filter(lambda x: x not in ['co2', 'projected-co2'], fileChoices)]


  parser = argparse.ArgumentParser(
    formatter_class = argparse.RawDescriptionHelpFormatter,

      description=textwrap.dedent('''\
        Creates a set of input files for dvmdostem.

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/
                {0}

        <OUTDIR>/<TAG>_<YSIZE>x<XSIZE>/output/restart-eq.nc

        Assumes a certain layout for the source files. At this point, the 
        source files are generally .tifs that have been created for the IEM
        project. As of Oct 2018 the is desgined to work with the data on 
        the atlas server:

        atlas:/atlas_scratch/ALFRESCO/ALFRESCO_Master_Dataset_v2_1/ALFRESCO_Model_Input_Datasets/IEM_for_TEM_inputs/

        **THE PATHS IN THIS SCIRPT MUST BE EDITED BY HAND IF IT IS TO BE RUN ON
        A DIFFERENT COMPUTER OR IF THE DIRECTORY LAYOUT ON ATLAS CHANGES!**


        There is a command line option to print an example slurm script or
        generate a set of slurm scripts from a csv file.
        '''.format("\n                ".join([i+'.nc' for i in fileChoices]))),

      epilog=textwrap.dedent(''''''),
  )
  
  parser.add_argument('--crtf-only', action="store_true",
      help=textwrap.dedent("""(DEPRECATED - now built into dvmdostem) Only 
        create the restart template file."""))

  parser.add_argument('--tifs', default="", required=False,
      help=textwrap.dedent("""Directory containing input TIF directories. This
        is used as a "base path", and it is assumed that all the requsite input
        files exist somewhere within the directory specified by this option.
        Using '/' as the --tifs argument allows absolute path specification in
        the config object in cases where required input files are not all
        contained within one directory. 
        (default: '%(default)s')"""))

  parser.add_argument('--outdir', default="input-staging-area",
      help=textwrap.dedent("""Directory for netCDF output files. 
        (default: '%(default)s')"""))

  parser.add_argument('--tag',
      help=textwrap.dedent("""A name for the dataset, used to name output 
        directory. (default: '%(default)s')"""))

  parser.add_argument('--years', type=int,
      help=textwrap.dedent("""The number of years of the climate data to 
        process. Use -1 to run for all TIFs found in input directory. 
        (default: %(default)s)"""))

  parser.add_argument('--start-year', default=0, type=int,
      help=textwrap.dedent("""An offset to use for making a climate dataset 
        that doesn't start at the beginning of the historic (1901) or projected
        (2001) datasets. Mostly deprecated in favor of --clip-projected2match-historic"""))

  parser.add_argument('--buildout-time-coord', action='store_true',
      help=textwrap.dedent('''Add a time coordinate variable to the *-climate.nc 
        files. Also populates the coordinate variable attributes.'''))

  parser.add_argument('--xoff', type=float,
      help="source window offset for x axis (default: %(default)s)")
  parser.add_argument('--yoff', type=float,
      help="source window offset for y axis (default: %(default)s)")

  parser.add_argument('--xsize', type=int,
      help="source window x size (default: %(default)s)")
  parser.add_argument('--ysize', type=int,
      help="source window y size (default: %(default)s)")

  parser.add_argument('--lonlat', action='store_true',
    help=textwrap.dedent('''When this is specified, the x and y offset values
      are assumed to be in WGS84 longitude and latitude, i.e. -154.324 68.23
      (Pixel/Line offsets are the default assumption). This option is mutually
      exclusive with --projwin.'''))

  parser.add_argument('--projwin', action='store_true',
    help=textwrap.dedent('''When this is specified, the x and y offset values
      are assumed to be in projection coordinates (Pixel/Line offsets are the
      default assumption). This option is mutually exclusive with --lonlat.'''))

  parser.add_argument('--which', default=['all'], nargs='+',
      choices=fileChoices+['all'], metavar='FILE',
      help=textwrap.dedent('''Space separated list of which files to create. 
        Allowed values: {:}. (default: %(default)s)'''.format(', '.join(fileChoices+['all']))))

  parser.add_argument('--clip-projected2match-historic', action='store_true',
    help=textwrap.dedent('''Instead of building the entire projected dataset, 
      start building it where the historic 
      data leaves off.'''))

  parser.add_argument('--withproj', action='store_true',
    help=textwrap.dedent('''Copy projection information into resultant netcdf
      files. Included x and y projection variables as well as all available
      projection information stored in netcdf attributes.'''))

  parser.add_argument('--withlatlon', action='store_true',
    help=textwrap.dedent('''Generate latitude and longitude variables and
      include in the resultant netcdf files.'''))

  parser.add_argument('--cleanup', action='store_true', 
    help=textwrap.dedent('''Tries to clean up any temporary files created in 
      the process. It can be useful to leave the files around for debugging
      purposes.'''))

  parser.add_argument('--slurm-wrapper', action='store_true',
      help=textwrap.dedent('''Writes the file "CRI_slurm_wrapper.sh" and exits.
        Submit CRI_slurm_wrapper.sh to slurm using sbatch. Expected workflow
        is that you will generate the slurm wrapper script and then edit the
        script as needed (uncommenting the lines for the desired site and post
        processing steps that you want).''')) 

  parser.add_argument('--slurm-wrappers-from-csv',
    help=textwrap.dedent('''Generates a slurm wrapper script for every line in
      a csv file. Assumes csv file has header line and fields: site, lon, lat.
      Scripts will be named like: "cri_slurm_wrapper_NNNN.sh" with N
      incrementing according to rows in the csv file.'''))

  parser.add_argument('--dump-empty-config', action='store_true',
      help=textwrap.dedent('''Write out an empty config file with all the keys
        that need to be filled in to make a functioning config object.'''))

  parser.add_argument('--projected-climate-config', nargs=1, choices=['ncar-ccsm4', 'mri-cgcm3'],
      help=textwrap.dedent('''Choose a configuration to use for the projected 
        climate data.'''))

  print "Parsing command line arguments..."
  args = parser.parse_args()
  print "args: ", args


  if args.lonlat and args.projwin:
    parser.error("Argument ERROR!: Must specify only one of --projwin and --lonlat!")

  print "Reading config file..."
  config = configobj.ConfigObj(base_ar5_rcp85_config.split("\n"))


  if args.slurm_wrapper:
    ofname = 'CRI_slurm_wrapper.sh'
    print "Writing wrapper file: {}".format(ofname)
    print "Submit using sbatch."
    with open(ofname, 'w') as f:
      f.write(get_slurm_wrapper_string(args.tifs))
    exit(0)

  if args.slurm_wrappers_from_csv:

    if not args.projected_climate_config:
      parser.error("Argument ERROR!: Must specify projected climate when using --slurm-wrappers-from-csv!")

    with open(args.slurm_wrappers_from_csv) as csvfile:
      reader = csv.DictReader(csvfile)
      sites = list(reader)

    for i, site in enumerate(sites):

      slurm_wrapper_string = get_slurm_wrapper_string(
        tifs=args.tifs, 
        pclim=args.projected_climate_config[0],
        sitename=site['site'],
        xoff=site['lon'], yoff=site['lat'],
        xsize=10, ysize=10,
        coordtype="--lonlat \\"
        )

      with open("cri_slurm_wrapper_{:04d}.sh".format(i), 'w') as outfile:
        outfile.write(slurm_wrapper_string)

    print "Now submit all your wrappers with a for loop! GOOD LUCK!"
    exit(0)


  if args.dump_empty_config:
    ofname = "EMPTY_CONFIG_create_region_input.txt"
    print "Writing empty config file: {}".format(ofname)
    ec = get_empty_config_object()
    ec.filename = ofname
    ec.write()
    exit(0)


  # Verify argument combinations: time coordinate variables and files
  if args.clip_projected2match_historic:
    if (('historic-climate' in args.which) and ('projected-climate' in args.which)) or (('co2' in args.which) and ('projected-co2' in args.which)):
      pass # everything ok...
    elif 'all' in args.which:
      pass # everything ok...
    else:
      print "ERROR!: Can't clip the projected climate to start where the "
      print "        historic data leaves off unless creating both historic "
      print "        and projected files!"
      exit(-1)
    if (args.buildout_time_coord):
      pass # everything ok...
    else:
      if ('historic-climate' in args.which) and ('projected-climate' in args.which):
        print "ERROR!: You MUST specify to the --buildout-time-coord option if you want to match historic and projected climate files!"
        exit(-1)
      elif ('co2' in args.which) and ('projected-co2' in args.which):
        pass # No need for build out time coord for co2 files.
      else:
        print "ERROR?? Not sure what the problem is..."
        exit(-1)
    if args.start_year > 0:
      print "WARNING! The --start-year offset will be ignored for projected climate file!"


  # Verify argument combinations: spatial and time dims, required paths 
  # for source datafiles...
  which_files = args.which
  if 'all' in which_files:
    print "Will generate ALL input files."
    which_files = fileChoices

  if any( [f in temporal_file_choices for f in which_files] ):
    if not all([x is not None for x in [args.years, args.start_year]]):
      print args
      print args.which
      print which_files
      parser.error("Argument ERROR!: Must specify years and start year for temporal files!")

  if any( [f in spatial_file_choices for f in which_files] ):
    if not all([x is not None for x in [args.xoff, args.yoff, args.xsize, args.ysize, args.tifs]]):
      print args
      print args.which
      print which_files
      parser.error("Argument ERROR!: Must specify ALL sizes and offsets for spatial files!")

  if any(f for f in which_files if f != 'co2'):
    verify_paths_in_config_dict(args.tifs, config)

  # Verify argument combos: project climate configuration specified when 
  # asking to generate projected climate
  if 'projected-climate' in which_files or 'projected-co2' in which_files:
    if args.projected_climate_config is not None:
      pass # All ok - value is set and the choices are constrained above
    else:
      parser.error("Argument ERROR! Must specify a projecte climate configuration for the projected-climate file!")

  # Pick up the user's config option for which projected climate to use 
  # overwrite the section in the config object.
  cmdline_config = configobj.ConfigObj()
  if 'projected-climate' in which_files or 'projected-co2' in which_files:
    if 'ncar-ccsm4' in args.projected_climate_config:
      cmdline_config = configobj.ConfigObj(ncar_ccsm4_ar5_rcp85_config.split("\n"))
    elif 'mri-cgcm3' in args.projected_climate_config:
      cmdline_config = configobj.ConfigObj(mri_cgcm3_ar5_rcp85_config.split("\n"))

  config.merge(cmdline_config)

  print "\n".join(config.write())

  years = args.years
  start_year = args.start_year
  

  if args.lonlat:
    # convert from lon, lat to x, y projection coordinates
    xo, yo, _ = xform(args.xoff, args.yoff)
    yo = yo - 500 # Not sure what is up with this, but if we don't 
                  # take 500m off the y offset (projection coords) then we 
                  # end up with the lon/lat point consistently in the pixel just
                  # below the cropped area.

    coords_are_projection = True

  elif args.projwin:
    xo = args.xoff
    yo = args.yoff
    coords_are_projection = True

  else:  
    xo = args.xoff
    yo = args.yoff
    coords_are_projection = False

  xs = args.xsize
  ys = args.ysize

  tif_dir = args.tifs;
  print "Will be looking for files in:      ", tif_dir

  if args.tag is None:
    parser.error("--tags must be defined inorder to proceed!")

  # Like this: somedirectory/sometag_NxM
  out_dir = os.path.join(args.outdir, "%s_%sx%s" % (args.tag, ys, xs))
  print "Will be (over)writing files to:    ", out_dir
  if not os.path.exists(out_dir):
    os.makedirs(out_dir)

  # All we are doing is creating a restart template file, then quitting.
  if args.crtf_only:
    if not os.path.exists( os.path.join(out_dir, "output") ):
      os.mkdir(os.path.join(out_dir, "output"))

    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-eq.nc"), sizey=ys, sizex=xs)
    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-sp.nc"), sizey=ys, sizex=xs)
    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-tr.nc"), sizey=ys, sizex=xs)
    create_template_restart_nc_file(os.path.join(out_dir, "output/restart-sc.nc"), sizey=ys, sizex=xs)
    exit()



  print type(start_year), type(years)
  main(start_year, years, xo, yo, xs, ys, tif_dir, out_dir,
       files=which_files,
       config=config,
       time_coord_var=args.buildout_time_coord, 
       clip_projected2match_historic=args.clip_projected2match_historic,
       withlatlon=args.withlatlon,
       withproj=args.withproj,
       projwin=coords_are_projection,
       cleanup=args.cleanup)



