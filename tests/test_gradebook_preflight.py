from sqlalchemy import JSON, Column, Integer, MetaData, String, Table, create_engine, insert

from calculateur.services.gradebook_preflight import preflight_gradebooks


def test_preflight_counts_valid_profiles_and_rejects_invalid_data():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    visitors = Table(
        "anonymous_visitors",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("public_id", String(36), nullable=False),
        Column("data", JSON, nullable=False),
    )
    metadata.create_all(engine)
    valid = {"notes": {"Maths": [{"note": 15, "bareme": 20}]}, "coef": {"Maths": 3}}
    invalid = {"notes": {"Maths": [{"note": 25, "bareme": 20}]}, "coef": {"Maths": 3}}

    with engine.begin() as connection:
        connection.execute(
            insert(visitors),
            [
                {"id": 1, "public_id": "valid", "data": valid},
                {"id": 2, "public_id": "invalid", "data": invalid},
            ],
        )
        report = preflight_gradebooks(connection, batch_size=1)

    assert report["profiles"] == 2
    assert report["valid_profiles"] == 1
    assert report["subjects"] == 1
    assert report["grades"] == 1
    assert report["subject_average_sum"] == 15
    assert report["overall_average_sum"] == 15
    assert report["profiles_with_issues"] == 1
    assert report["issues"][0]["visitor_id"] == 2
    engine.dispose()


def test_preflight_reports_empty_database_without_writes():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        report = preflight_gradebooks(connection)

    assert report["source_table_found"] is False
    assert report["profiles"] == 0
    assert report["profiles_with_issues"] == 0
    engine.dispose()
