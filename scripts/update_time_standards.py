from pathlib import Path
from urllib.parse import urljoin
import html

import requests
from bs4 import BeautifulSoup


SOURCE_URL = (
    "https://www.gomotionapp.com/team/wzielsc/page/"
    "times/links-to-time-standards"
)

OUTPUT_FILE = Path("time-standards/index.html")


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(text):
    return " ".join(text.split())


def absolute(url):
    return urljoin(SOURCE_URL, url)


def find_heading(soup, text):
    """Find a heading containing the requested text."""
    wanted = text.lower()

    for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
        value = clean(tag.get_text(" ", strip=True)).lower()

        if wanted in value:
            return tag

    return None


def parse_table(table, link_cell=0):
    """
    Read a GoMotion table.

    link_cell:
      0  = link is in Meet column
      -1 = link is in final Time Standards column
    """

    items = []

    if table is None:
        return items

    rows = table.find_all("tr")

    for row in rows:
        cells = row.find_all(["td", "th"])

        if not cells:
            continue

        values = [
            clean(cell.get_text(" ", strip=True))
            for cell in cells
        ]

        # Skip header rows
        joined = " ".join(values).lower()

        if (
            ("meet" in joined and "date" in joined)
            or "time standard(s)" in joined
        ):
            continue

        title = values[0] if len(values) > 0 else ""
        date = values[1] if len(values) > 1 else ""
        location = values[2] if len(values) > 2 else ""

        if not title:
            continue

        try:
            link_source = cells[link_cell]
        except IndexError:
            link_source = cells[0]

        link = link_source.find("a", href=True)

        items.append(
            {
                "title": title,
                "date": date,
                "location": location,
                "url": absolute(link["href"]) if link else None,
            }
        )

    return items


def make_card(title, date="", location="", url=None):
    meta = " · ".join(
        part for part in [date, location] if part
    )

    if url:
        return f"""
<a class="standard-card"
   href="{html.escape(url)}"
   target="_blank"
   rel="noopener">

  <div class="standard-main">
    <strong>{html.escape(title)}</strong>
    {
        '<span>' + html.escape(meta) + '</span>'
        if meta else ''
    }
  </div>

  <div class="standard-action">
    VIEW STANDARDS →
  </div>

</a>
"""

    return f"""
<div class="standard-card unavailable">

  <div class="standard-main">
    <strong>{html.escape(title)}</strong>
    {
        '<span>' + html.escape(meta) + '</span>'
        if meta else ''
    }
  </div>

  <div class="standard-pending">
    TIME STANDARDS NOT YET PUBLISHED
  </div>

</div>
"""


# ---------------------------------------------------------
# DOWNLOAD + PARSE IES PAGE
# ---------------------------------------------------------

def main():

    print("Downloading Inland Empire Swimming time standards...")

    response = requests.get(
        SOURCE_URL,
        timeout=30,
        headers={
            "User-Agent":
                "Mozilla/5.0 CougarAquatics-TimeStandards/1.0"
        },
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")


    # -----------------------------------------------------
    # USA SWIMMING MOTIVATIONAL STANDARDS
    # -----------------------------------------------------

    motivational_heading = find_heading(
        soup,
        "USA Swimming Motivational Time Standards"
    )

    motivational_url = None
    motivational_title = (
        "2024–2028 USA SWIMMING MOTIVATIONAL TIME STANDARDS"
    )

    if motivational_heading:
        links = motivational_heading.find_all(
            "a",
            href=True
        )

        if links:
            # The final link contains the actual standards PDF
            motivational_url = absolute(
                links[-1]["href"]
            )


    # -----------------------------------------------------
    # REGIONAL / NATIONAL MEETS
    # -----------------------------------------------------

    regional_heading = find_heading(
        soup,
        "Local/Zone/Sectional/National Meets"
    )

    regional_table = (
        regional_heading.find_next("table")
        if regional_heading
        else None
    )

    # On the current IES page the time-standard link
    # is attached to the MEET NAME.
    regional_items = parse_table(
        regional_table,
        link_cell=0
    )


    # -----------------------------------------------------
    # IES CHAMPIONSHIP MEETS
    # -----------------------------------------------------

    ies_heading = find_heading(
        soup,
        "IES Championship Meets"
    )

    ies_table = (
        ies_heading.find_next("table")
        if ies_heading
        else None
    )

    # IES Championship tables put standards in
    # the final column.
    ies_items = parse_table(
        ies_table,
        link_cell=-1
    )


    # -----------------------------------------------------
    # HIGH SCHOOL STANDARDS
    # -----------------------------------------------------

    high_school_heading = find_heading(
        soup,
        "High School State Time Standards"
    )

    high_school_url = None
    high_school_title = (
        "WASHINGTON HIGH SCHOOL STATE TIME STANDARDS"
    )

    if high_school_heading:

        node = high_school_heading.find_next()

        while node:

            if (
                node.name in ["h1", "h2", "h3", "h4"]
                and node is not high_school_heading
            ):
                break

            if node.name == "a" and node.get("href"):

                text = clean(
                    node.get_text(" ", strip=True)
                )

                if text:
                    high_school_title = text

                high_school_url = absolute(
                    node["href"]
                )

                # Use the first meaningful linked standard
                break

            node = node.find_next()


    # -----------------------------------------------------
    # BUILD CARDS
    # -----------------------------------------------------

    regional_cards = "\n".join(
        make_card(
            item["title"],
            item["date"],
            item["location"],
            item["url"],
        )
        for item in regional_items
    )

    ies_cards = "\n".join(
        make_card(
            item["title"],
            item["date"],
            item["location"],
            item["url"],
        )
        for item in ies_items
    )


    motivational_card = make_card(
        motivational_title,
        url=motivational_url
    )

    high_school_card = make_card(
        high_school_title,
        url=high_school_url
    )


    # -----------------------------------------------------
    # OUTPUT PAGE
    # -----------------------------------------------------

    page = f"""<!doctype html>

<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Cougar Aquatics Time Standards</title>


<style>

:root {{
  --crimson: #981e32;
  --ink: #20242a;
  --text: #565d64;
  --muted: #767c82;
  --card: #f1f2f3;
  --card-hover: #e7e9eb;
  --line: #dddddd;
}}


* {{
  box-sizing: border-box;
}}


html,
body {{
  margin: 0;
  padding: 0;

  background: #ffffff;

  color: var(--ink);

  font-family:
    Arial,
    Helvetica,
    sans-serif;
}}


.page {{
  width: 100%;
  max-width: 1100px;

  margin: 0 auto;

  padding: 22px 16px 36px;
}}


/* HEADER */

.eyebrow {{
  margin: 0 0 7px;

  color: var(--crimson);

  font-size: 11px;
  font-weight: 800;

  letter-spacing: 2px;
}}


h1 {{
  margin: 0 0 8px;

  color: var(--ink);

  font-size: 36px;
  line-height: 1;

  font-weight: 800;

  letter-spacing: -1px;
}}


.intro {{
  margin: 0;

  max-width: 600px;

  color: var(--text);

  font-size: 15px;
  line-height: 1.5;
}}


/* SECTIONS */

.section {{
  margin-top: 30px;
}}


.section h2 {{
  margin: 0 0 12px;

  padding-bottom: 7px;

  color: var(--ink);

  border-bottom:
    2px solid var(--crimson);

  font-size: 19px;
  line-height: 1.2;

  font-weight: 800;
}}


/* CARDS */

.grid {{
  display: grid;

  grid-template-columns:
    repeat(2, minmax(0, 1fr));

  gap: 8px;
}}


.standard-card {{
  min-height: 58px;

  padding: 13px 14px;

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 14px;

  background: var(--card);

  border-radius: 6px;

  color: var(--ink);

  text-decoration: none;
}}


a.standard-card {{
  transition:
    background .18s ease,
    transform .18s ease;
}}


a.standard-card:hover {{
  background: var(--card-hover);

  transform: translateY(-2px);
}}


.standard-main {{
  min-width: 0;
}}


.standard-main strong {{
  display: block;

  color: var(--ink);

  font-size: 12px;
  line-height: 1.25;

  font-weight: 800;
}}


.standard-main span {{
  display: block;

  margin-top: 4px;

  color: var(--muted);

  font-size: 10px;
  line-height: 1.3;
}}


.standard-action {{
  flex: 0 0 auto;

  color: var(--crimson);

  font-size: 9px;
  line-height: 1.2;

  font-weight: 800;

  white-space: nowrap;
}}


/* UNPUBLISHED */

.unavailable {{
  opacity: .72;
}}


.standard-pending {{
  flex: 0 0 auto;

  max-width: 150px;

  color: var(--muted);

  font-size: 9px;
  line-height: 1.2;

  font-weight: 800;

  text-align: right;
}}


/* SOURCE */

.source {{
  margin: 32px 0 0;

  padding-top: 14px;

  border-top: 1px solid var(--line);

  color: var(--muted);

  font-size: 11px;
  line-height: 1.5;
}}


.source a {{
  color: var(--crimson);

  font-weight: 700;

  text-decoration: none;
}}


/* MOBILE */

@media (max-width: 700px) {{

  .page {{
    padding:
      18px 10px 28px;
  }}


  h1 {{
    font-size: 30px;
  }}


  .intro {{
    font-size: 14px;
  }}


  .grid {{
    grid-template-columns: 1fr;
  }}


  .standard-card {{
    min-height: 55px;

    padding: 12px;
  }}

}}


@media (max-width: 430px) {{

  .standard-card {{
    display: block;
  }}


  .standard-action,
  .standard-pending {{
    display: block;

    max-width: none;

    margin-top: 6px;

    text-align: left;
  }}

}}

</style>

</head>


<body>

<main class="page">


<header>

  <p class="eyebrow">
    SWIMMER RESOURCES
  </p>

  <h1>
    TIME STANDARDS
  </h1>

  <p class="intro">
    Current qualifying and motivational time standards
    for Cougar Aquatics swimmers.
  </p>

</header>



<section class="section">

  <h2>
    USA SWIMMING
  </h2>

  <div class="grid">

    {motivational_card}

  </div>

</section>



<section class="section">

  <h2>
    REGIONAL &amp; NATIONAL MEETS
  </h2>

  <div class="grid">

    {regional_cards}

  </div>

</section>



<section class="section">

  <h2>
    IES CHAMPIONSHIP MEETS
  </h2>

  <div class="grid">

    {ies_cards}

  </div>

</section>



<section class="section">

  <h2>
    HIGH SCHOOL
  </h2>

  <div class="grid">

    {high_school_card}

  </div>

</section>



<p class="source">

  Standards and source information maintained by

  <a
    href="{SOURCE_URL}"
    target="_blank"
    rel="noopener">

    Inland Empire Swimming

  </a>.

</p>


</main>

</body>

</html>
"""


    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        page,
        encoding="utf-8"
    )


    print(
        f"Wrote {OUTPUT_FILE}"
    )

    print(
        f"Regional / national meets: "
        f"{len(regional_items)}"
    )

    print(
        f"IES championship meets: "
        f"{len(ies_items)}"
    )


if __name__ == "__main__":
    main()
