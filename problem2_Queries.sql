USE library;

-- F2.1
SELECT B.book_id, B.title, B.price, C.name AS category
FROM BOOK AS B
JOIN CATEGORY AS C ON B.category_id = C.category_id
WHERE B.title LIKE '%Palace%'
  AND B.price BETWEEN 15 AND 20
  AND C.category_id = 1
ORDER BY B.price ASC, B.book_id ASC;

-- F2.2
SELECT B.book_id, B.title, B.price, B.publish_year, A.name AS author, P.name AS publisher, C.name AS category
FROM BOOK AS B
JOIN AUTHOR AS A ON B.author_id = A.author_id
JOIN PUBLISHER AS P ON B.publisher_id = P.publisher_id
JOIN CATEGORY AS C ON B.category_id = C.category_id
ORDER BY B.book_id;

-- F2.3 (a)
SELECT C.name AS category, COUNT(B.book_id) AS books, AVG(B.price) AS average_price
FROM CATEGORY AS C
LEFT OUTER JOIN BOOK AS B ON C.category_id = B.category_id
GROUP BY C.category_id, C.name
ORDER BY C.category_id;

-- F2.3 (b)
SELECT A.name AS author, COUNT(B.book_id) AS books
FROM AUTHOR AS A
JOIN BOOK AS B ON A.author_id = B.author_id
GROUP BY A.author_id, A.name
HAVING COUNT(B.book_id) >= 2
ORDER BY A.author_id;

-- F2.3 (c)
SELECT SUM(price) AS total_price, MIN(price) AS smallest_price, MAX(price) AS largest_price
FROM BOOK;

-- F2.4 (a)
SELECT L.loan_id, B.title, M.name AS member, L.loan_date
FROM LOAN AS L
JOIN BOOK AS B ON L.book_id = B.book_id
JOIN MEMBER AS M ON L.member_id = M.member_id
WHERE L.return_date IS NULL
ORDER BY L.loan_id;

-- F2.4 (b)
SELECT M.member_id, M.name, M.email
FROM MEMBER AS M
LEFT OUTER JOIN LOAN AS L ON M.member_id = L.member_id
WHERE L.loan_id IS NULL
ORDER BY M.member_id;

-- F2.4 (c)
SELECT B.book_id, B.title
FROM BOOK AS B
LEFT OUTER JOIN LOAN AS L ON B.book_id = L.book_id
WHERE L.loan_id IS NULL
ORDER BY B.book_id;

-- F2.5 (a)
SELECT B.book_id, B.title, COUNT(L.loan_id) AS loans
FROM BOOK AS B
JOIN LOAN AS L ON B.book_id = L.book_id
GROUP BY B.book_id, B.title
ORDER BY loans DESC, B.book_id
LIMIT 3;

-- F2.5 (b)
SELECT M.member_id, M.name, COUNT(L.loan_id) AS loans
FROM MEMBER AS M
JOIN LOAN AS L ON M.member_id = L.member_id
GROUP BY M.member_id, M.name
ORDER BY loans DESC, M.member_id
LIMIT 1;

-- F2.6 (a)
SELECT A.author_id, A.name, COUNT(B.book_id) AS books
FROM AUTHOR AS A
LEFT OUTER JOIN BOOK AS B ON A.author_id = B.author_id
GROUP BY A.author_id, A.name
ORDER BY A.author_id;

-- F2.6 (b)
SELECT B.title, A.name AS author, P.name AS publisher, A.country
FROM BOOK AS B
JOIN AUTHOR AS A ON B.author_id = A.author_id
JOIN PUBLISHER AS P ON B.publisher_id = P.publisher_id
WHERE A.country = P.country
ORDER BY B.book_id;

