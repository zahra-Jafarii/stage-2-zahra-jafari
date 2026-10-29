from sqlalchemy import text


def list_purchase_months(engine):
    sql = text(
        "SELECT DISTINCT date_trunc('month', order_purchase_timestamp)::date AS month_start "
        "FROM olist.orders ORDER BY 1"
    )
    with engine.connect() as connection:
        return [row.month_start for row in connection.execute(sql)]


def rebuild_month(connection, month_start):
    connection.execute(
        text("CALL olist.rebuild_monthly_snapshot(:month_start)"),
        {"month_start": month_start},
    )


def rebuild_all_snapshots(engine):
    months = list_purchase_months(engine)
    with engine.begin() as connection:
        for month_start in months:
            rebuild_month(connection, month_start)
    return len(months)
