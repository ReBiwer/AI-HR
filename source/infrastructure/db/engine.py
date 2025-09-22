from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from source.infrastructure.settings.app import app_settings

engine = create_async_engine(app_settings.db_url)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
