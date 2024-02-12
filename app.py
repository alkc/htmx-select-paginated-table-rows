#!/usr/bin/env python3

# app.py
from flask import Flask, render_template, request, abort, make_response
from io import StringIO

import csv
import math


app = Flask(__name__)

db: list[dict] = []

with open("data.csv", "r") as csvfile:
    csv_data = csv.DictReader(csvfile)
    db = list(csv_data)


def get_table_rows(
    data: list[dict],
    page_nbr: int = 1,
    rows_per_page: int = 30,
    search_string: str | None = None,
):
    """
    Search and return paginated table data
    """
    filtered_rows = []
    start_point = (page_nbr - 1) * rows_per_page

    print(start_point)

    if search_string:
        search_string = search_string.lower()
        print(search_string)

        for row in data:
            if any(search_string in val.lower() for val in row.values()):
                print(row)
                filtered_rows.append(row)

        # @_@
        filtered_rows, nbr_search_matches = get_table_rows(
            filtered_rows, page_nbr, rows_per_page, None
        )
        return filtered_rows, nbr_search_matches

    for row_idx, row in enumerate(data):
        if row_idx in range(start_point, start_point + rows_per_page):
            filtered_rows.append(row)

    return filtered_rows, len(data)


@app.route("/", methods=["GET", "POST"])
def index():
    target_template = "index.html"

    selected_page_nbr = int(request.args.get("page", 1))
    selected_limit_nbr = int(request.args.get("limit", 10))
    search = request.args.get("search", None)
    selected_rows = set()

    app.logger.debug("Request headers:\t%s", request.headers)

    if request.method == "POST":
        app.logger.debug(request.form)
        hx_target = request.headers.get("Hx-Target")
        match hx_target:
            case "table-container":
                target_template = "table.html"
            case _:
                return abort(400)

        selected_limit_nbr = int(request.form.get("limit", 10))
        selected_page_nbr = int(request.form.get("page", 1))
        search = request.form.get("search", None)
        selected_rows = set(request.form.getlist("selected-rows"))

    db_data, nbr_total = get_table_rows(db, selected_page_nbr, selected_limit_nbr, search)

    if (selected_page_nbr * selected_limit_nbr) > nbr_total:
        selected_page_nbr = 1

    available_pages = math.ceil(nbr_total / selected_limit_nbr)

    return render_template(
        target_template,
        db_data=db_data,
        selected_rows=selected_rows,
        nbr_pages=available_pages,
        nbr_limit=selected_limit_nbr,
        selected_page=selected_page_nbr,
    )


@app.post("/tsv")
def create_tsv_report():
    """Process list of db ids into TSV download"""

    selected_rows = set(request.form.getlist("selected-rows"))

    app.logger.debug(f"Processing {selected_rows} into TSV")

    si = StringIO()
    writer = csv.DictWriter(
        si,
        fieldnames=["first_name", "last_name", "favorite_food"],
        extrasaction="ignore",
        delimiter="\t",
    )
    writer.writeheader()
    for row in db:
        if (curr_id := row.get("id")) in selected_rows:
            writer.writerow(row)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.tsv"
    output.headers["Content-type"] = "text/tsv"
    return output


if __name__ == "__main__":
    app.run(debug=True)
