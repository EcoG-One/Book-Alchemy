from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class Author(db.Model):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    birth_date: Mapped[str]
    date_of_death: Mapped[Optional[str]]

    books = relationship("Book", back_populates="author")

    def __repr__(self):
        return f"Author({self.id}, {self.name})"

    def __str__(self):
        return (f"Author: {self.name} ID: {self.id} "
               f"Birth Day: {self.birth_date} Death Day: {self.date_of_death}")


class Book(db.Model):
    __tablename__ = "books"

    book_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isbn: Mapped[int] = mapped_column(unique=True)
    title: Mapped[str]
    publication_year: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    summary: Mapped[str]
    img_url: Mapped[str]
    rating: Mapped[int]

    author = relationship("Author", back_populates="books")

    def __repr__(self):
        return f"<Book(id={self.book_id}, title='{self.title}')>"

    def __str__(self):
        return (
            f"Book ID: {self.book_id}, Title: {self.title}, "
            f"Year: {self.publication_year}, ISBN: {self.isbn}"
        )


    @classmethod
    def count_books(cls, session):
        """
        Returns the total number of books in the database.
        :param session: The SQLAlchemy session to query the database.
        :return: Number of books.
        """
        return session.query(cls).count()
