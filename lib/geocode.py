# Non_US http://earth-info.nga.mil/gns/html/gis_countryfiles.htm
# US     http://geonames.usgs.gov/domestic/download_data.htm

# NEED TO DO...
# CREATE INDEX IF NOT EXISTS idx_ctc0 ON gnsloc (SORT_NAME, CC1);

import datetime, csv, os, re, sqlite3

# We need to import these one at a time because many of these functions are
# duplicated in multiple places. That is, there are 3 or 4 identical or
# slightly different versions located in different files.
#from fwork import *
from fwork import jarow
from fwork import cityctry
from fwork import tblExist


# geocode_replace_loc consists of a series of functions,
# each with a SQL statement that is passed as a parameter
# to replace_loc. Uses temporary tables for handling
# intermediate relations.
from geocode_replace_loc import *

# TODO: switch to import the tested version of sep_wrd.
from sep_wrd_geocode import sep_wrd


conn = sqlite3.connect("hashTbl.sqlite3")
c = conn.cursor()
# TODO: Consider replacing the lambdas with functions which can be tested.
conn.create_function("blk_split", 1, lambda x: re.sub(" ", "", x))
conn.create_function("sep_cnt",   1, lambda x: len(re.findall("[,|]", x)))
conn.create_function("jarow",     2, jarow)
conn.create_function("cityctry",  3, cityctry)
conn.create_function("sep_wrd",   2, sep_wrd)
conn.create_function("rev_wrd",   2, lambda x,y:x.upper()[::-1][:y])


# TODO: cover geocode setup functions with unit tests.
from geocode_setup import *

print datetime.datetime.now()
geocode_db_initialize(c)
loc_create_table(c)
if not(tblExist(c, "locMerge")):
    fix_city_country(c)
    fix_state_zip(c)
    create_loc_indexes(conn)

create_usloc_table(c)
create_locMerge_table(c)
print datetime.datetime.now()

# End of setup.


def print_loc_and_merge(c):
    VarX = c.execute("select count(*) from loc").fetchone()[0]
    VarY = c.execute("select count(*) from locMerge").fetchone()[0]
    print " - Loc =", VarX, " OkM =", VarY, " Total =", VarX+VarY, "  ", datetime.datetime.now()


# TODO: Unit test extensively.
def replace_loc(script):

    c.execute("DROP TABLE IF EXISTS temp1")
    c.execute("CREATE TEMPORARY TABLE temp1 AS %s" % script)
    # Apparently, this tmp1_idx is either superfluous or redundant.
    #c.execute("CREATE INDEX IF NOT EXISTS tmp1_idx ON temp1 (CityA, StateA, CountryA, ZipcodeA)")

    #print_table_info(c)

    # TODO: Which tables will pass this conditional?
    if table_temp1_has_rows(c):
        create_loc_and_locmerge_tables(c)
        print_loc_and_merge(c)

    conn.commit()


# Prefixed tablename (loc) with with dbname (also loc)
print "Loc =", c.execute("select count(*) from loctbl.loc").fetchone()[0]

# TODO: Refactor the range call into it's own function, unit test
# that function extensively.
# TODO: Figure out what these hardcoded parameters mean.
for scnt in range(-1, c.execute("select max(sep_cnt(city)) from loctbl.loc").fetchone()[0]+1):

    sep = scnt
    print "------", scnt, "------"
    replace_loc(domestic_sql()                     % (sep, scnt))
    replace_loc(domestic_block_remove_sql()        % (sep, scnt))
    replace_loc(domestic_first3_jaro_winkler_sql() % (sep, sep, "10.92", scnt))
    replace_loc(domestic_last4_jaro_winkler_sql()  % (sep, sep, "10.90", scnt))
    replace_loc(foreign_full_name_1_sql()          % (sep, scnt))
    replace_loc(foreign_full_name_2_sql()          % (sep, scnt))
    replace_loc(foreign_short_form_sql()           % (sep, scnt))
    replace_loc(foreign_block_split_sql()          % (sep, scnt))
    replace_loc(foreign_first3_jaro_winkler_sql()  % (sep, sep, "20.92", scnt))
    replace_loc(foreign_last4_jaro_winkler_sql()   % (sep, sep, "20.90", scnt))

### End of for loop

print "------ F ------"

replace_loc(domestic_2nd_layer_sql())
replace_loc(domestic_first3_2nd_jaro_winkler_sql() % ("14.95"))
replace_loc(foreign_full_name_2nd_layer_sql())
replace_loc(foreign_full_nd_2nd_layer_sql())
replace_loc(foreign_no_space_2nd_layer_sql())
replace_loc(foreign_first3_2nd_jaro_winkler_sql()  % ("24.95"))
replace_loc(domestic_zipcode_sql())

conn.commit()
c.close()
conn.close()
