from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.sql.functions import col, when, lit
import logging
from typing import Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class SparkManager:
    """Manages Spark session and provides utility methods."""
    
    def __init__(self):
        self._spark: Optional[SparkSession] = None
    
    @property
    def spark(self) -> SparkSession:
        """Get or create Spark session."""
        if self._spark is None:
            self._spark = self._create_spark_session()
        return self._spark
    
    def _create_spark_session(self) -> SparkSession:
        """Create a new Spark session with configured settings."""
        return SparkSession.builder \
            .appName(settings.spark_app_name) \
            .master(settings.spark_master) \
            .config("spark.driver.memory", settings.spark_driver_memory) \
            .config("spark.executor.memory", settings.spark_executor_memory) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
    
    def stop(self):
        """Stop the Spark session."""
        if self._spark:
            self._spark.stop()
            self._spark = None


# Global Spark manager instance
spark_manager = SparkManager()
