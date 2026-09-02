#!/usr/bin/env bash
# Fetch the two halves of the EphemErr label factory for a range of days in 2025.
#   student input : broadcast navigation message (BKG)
#   manufacturer  : precise orbit + precise clock, reconstructed days later by ESA from a global
#                   tracking network the receiver has no access to
#
# Terms (docs/compliance/LICENSE_AUDIT.md, 2026-09-02 follow-up): the broadcast file is an IGS
# product served by BKG, an IGS Global Data Center, under the IGS Data and Product Disclaimer and
# Terms of Use (docs/compliance/sources/IGS_Data_and_Product_Disclaimer_and_Terms_of_Use_200805.txt):
# open to scientific, educational and commercial users, no cost or obligation, attribution
# required. Attribution: International GNSS Service (IGS) and its contributing organizations;
# BKG GNSS Data Center. The ESA final products are ESA's IGS Analysis Center products served from
# ESA's own web server, whose linked terms are ESA's general website terms; whether those govern
# the product directory COULD NOT be verified - see the audit. Nothing fetched here is committed.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/data/gnss"
mkdir -p "$DIR"
UA="raise-v1-research/1.0 (<contact: see the repository owner>)"
START=${1:-1}; END=${2:-21}; YEAR=2025
ok=0; miss=0
for doy in $(seq -w "$START" "$END"); do
  d=$((10#$doy))
  # GPS week/day-of-week for YEAR-doy, via the Julian day number
  read -r week dow < <(python3 -c "
import datetime
d=datetime.date($YEAR,1,1)+datetime.timedelta(days=$d-1)
def jdn(y,mo,dd):
    a=(14-mo)//12; yy=y+4800-a; mm=mo+12*a-3
    return dd+(153*mm+2)//5+365*yy+yy//4-yy//100+yy//400-32045
n=jdn(d.year,d.month,d.day)-2444245
print(n//7, n%7)")
  ddd=$(printf "%03d" "$d")
  b="$DIR/brdc_${ddd}.rnx.gz"; s="$DIR/sp3_${ddd}.SP3.gz"; c="$DIR/clk_${ddd}.CLK.gz"
  [ -s "$b" ] || curl -sS --max-time 120 -A "$UA" -o "$b" \
     "https://igs.bkg.bund.de/root_ftp/IGS/BRDC/${YEAR}/${ddd}/BRDC00IGS_R_${YEAR}${ddd}0000_01D_MN.rnx.gz" || true
  [ -s "$s" ] || curl -sS --max-time 180 -A "$UA" -o "$s" \
     "http://navigation-office.esa.int/products/gnss-products/${week}/ESA0OPSFIN_${YEAR}${ddd}0000_01D_05M_ORB.SP3.gz" || true
  [ -s "$c" ] || curl -sS --max-time 240 -A "$UA" -o "$c" \
     "http://navigation-office.esa.int/products/gnss-products/${week}/ESA0OPSFIN_${YEAR}${ddd}0000_01D_30S_CLK.CLK.gz" || true
  if [ -s "$b" ] && [ -s "$s" ] && [ -s "$c" ]; then ok=$((ok+1)); else miss=$((miss+1)); echo "  incomplete: doy $ddd (week $week)"; fi
done
echo "complete days: $ok   incomplete: $miss   in $DIR"
