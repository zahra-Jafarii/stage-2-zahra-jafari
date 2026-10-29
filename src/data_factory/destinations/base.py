from abc import ABC, abstractmethod


class BaseDestination(ABC):
    @abstractmethod
    def write_clean(self, table_name, chunk):
        """Insert valid rows; re-running must not duplicate them."""

    @abstractmethod
    def write_quarantine(self, table_name, chunk):
        """Store rejected rows together with their reason_code."""

    @abstractmethod
    def read_keys(self, table_name, column):
        """Return the set of existing key values of a column."""

    @abstractmethod
    def count_rows(self, table_name):
        """Return the number of rows in a table."""