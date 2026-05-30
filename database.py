from sqlalchemy import *

engine = create_engine(
    "sqlite:///data.db",
    connect_args={"check_same_thread": False}
)

metadata = MetaData()

companies = Table(
    "companies",
    metadata,

    Column("id", Integer, primary_key=True),

    Column("website_name", String),
    Column("company_name", String),
    Column("address", String),
    Column("mobile_number", String),

    Column("mail", Text),

    Column("core_service", Text),
    Column("target_customer", Text),

    Column("probable_pain_point", Text),
    Column("outreach_opener", Text)
)

metadata.create_all(engine)