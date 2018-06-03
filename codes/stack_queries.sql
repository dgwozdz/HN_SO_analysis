## Stackoverflow tags analysis

# stats per tag per day different technologies

SELECT
    cast(creationdate as date) post_date,
    tags,
    sum(score) score_sum,
    sum(viewcount) views,
    sum(answercount) answers,
    sum(favoritecount) favorites,
    sum(commentcount) comments,
    count(1) usage_cnt
FROM posts
WHERE  tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(creationdate as date), tags

SELECT
    cast(creationdate as date) post_date,
    tags,
    sum(score) score_sum,
    sum(viewcount) views,
    sum(answercount) answers,
    sum(favoritecount) favorites,
    sum(commentcount) comments,
    count(1) usage_cnt
FROM posts
WHERE  tags in ('<css>', '<html>',
			'<javascript>', '<php>', '<jquery>', '<go>', '<swift>', '<vba>',
             '<shell>', '<delphi>', '<cobol>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(creationdate as date), tags

SELECT
    cast(creationdate as date) post_date,
    tags,
    sum(score) score_sum,
    sum(viewcount) views,
    sum(answercount) answers,
    sum(favoritecount) favorites,
    sum(commentcount) comments,
    count(1) usage_cnt
FROM posts
WHERE  tags in ('<pascal>', '<fortran>', '<perl>', '<rust>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(creationdate as date), tags

SELECT
    cast(creationdate as date) post_date,
    tags,
    sum(score) score_sum,
    sum(viewcount) views,
    sum(answercount) answers,
    sum(favoritecount) favorites,
    sum(commentcount) comments,
    count(1) usage_cnt
FROM posts
WHERE  tags in ('<tensorflow>', '<d3.js>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(creationdate as date), tags
