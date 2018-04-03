## Stackoverflow tags analysis


# tags per day

SELECT
    cast(posts.creationdate as date) post_date,
    tags.TagName,
    COUNT(*) AS num_per_day 
FROM Tags
    INNER JOIN PostTags ON PostTags.TagId = Tags.id
    INNER JOIN Posts ON posts.ParentId = PostTags.PostId
WHERE  tags.TagName in ('r', 'python', 'java', 'scala', 'ruby', 'c',
            'c++', 'c#', 'spark', 'hadoop', 'sql', 'css', 'html',
			'javascript', 'php', 'jquery', 'go', 'swift', 'vba',
             'shell', 'delphi', 'cobol', 'pascal', 'fortran', 'perl', 'rust')
			and cast(posts.creationdate as date) between '2006-01-01' and '2017-12-31'
GROUP BY cast(posts.creationdate as date), Tags.TagName 
			
select distinct tags from posts where cast(creationdate as date) ='2006-01-01'

# views per day

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
WHERE  tags in ('<d3.js>', '<tensorflow>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(creationdate as date), tags

-- Stats for posts gathered throughout first 90 days since posts being published


SELECT
    p.id,
    cast(p.creationdate as date) post_date,
    tags,
	sum(score) score_sum,
    sum(iif(vt.id =2, 1, -1)) score_sum_90days,
    sum(viewcount) views,
    sum(answercount) answers,
    sum(favoritecount) favorites,
    sum(commentcount) comments,
    count(1) usage_cnt
FROM posts p
left join votes v
	on p.id = v.postid
left join votetypes vt
	on v.votetypeid = vt.id
WHERE  tags in ('<pascal>', '<fortran>', '<perl>', '<rust>')
			and cast(p.creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
		and vt.id in (2, 3)
group by p.id,cast(p.creationdate as date), tags


select v.postid, cast(p.creationdate as date) date, p.score, sum(iif(v.VoteTypeId =2, 1, -1))
	from votes v
	left join posts p
			on v.postid = p.id
			where p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
							'<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
			and p.posttypeid = 1 and v.VoteTypeId in (2, 3) 
			and datediff(d,cast(p.creationdate as date), cast(v.creationdate as date)) < 91
	group by v.postid, cast(p.creationdate as date), p.score
	
SELECT
    p.id,
    cast(p.creationdate as date) post_date,
    tags,
	sum(score) score_sum,
    sum(iif(vt.id =2, 1, -1)) score_sum_90days,
    sum(viewcount) views,
    sum(answercount) answers,
    sum(favoritecount) favorites,
    sum(commentcount) comments,
    count(1) usage_cnt
FROM posts p
left join (select postid, sum(iif(vt.id =2, 1, -1)) score from votes
              where votetypeid in (2,3)) votes v
	on p.id = v.postid
WHERE  tags in ('<pascal>', '<fortran>', '<perl>', '<rust>')
			and cast(p.creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
		and v.id in (2, 3) and p.id = 221170
group by p.id,cast(p.creationdate as date), tags



with (select p.tags, p.score, cast(v.creationdate as date) date,
	sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_90days
	from votes v
		left join posts p
		on p.id = v.postid
		and v.votetypeid in (2, 3)
		--and datediff(d, cast(p.creationdate as date),
                        --cast(v.creationdate as date)) < 91)
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>',
                            '<ruby>', '<c>',
                          '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
	group by p.tags, p.score, cast(v.creationdate as date)
)						v
select cast(p.creationdate as date) date,
  p.tags,
  p.score,
  p.favoritecount favorites,
  p.answercount answers,
  p.commentcount comments,
  count(a.id) answers_90days,
  sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_90days,
  sum(iif(v.VoteTypeId =5, 1, 0)) favourites_90days,
  count(c.id) comments_90days
  from posts p
  left join v
          on v.postid = p.id
	left join posts a
		on a.parentid = p.id
    left join comments c
        on c.postid = p.id
          where p.tags in ('<r>', '<python>', '<java>', '<scala>',
                            '<ruby>', '<c>',
                          '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
          and p.posttypeid = 1 and v.VoteTypeId in (2, 3, 5) 
          --and datediff(d, cast(p.creationdate as date),
          --                cast(v.creationdate as date)) < 91
          and datediff(d, cast(p.creationdate as date),
                          cast(a.creationdate as date)) < 91
          and datediff(d, cast(p.creationdate as date),
                          cast(c.creationdate as date)) < 91
		and a.posttypeid = 2
				
	group by cast(p.creationdate as date),
              p.tags,
              p.score,
              p.favoritecount,
              p.answercount,
              p.commentcount
			  
			  
			  
			  
			  
			  
			  
			  
			  
select p.tags, cast(p.creationdate as date) date,
a.id answer_id, v.votetypeid, c.id comment_id
  --count(a.id) answers_90days,
  --sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_90days,
  --sum(iif(v.VoteTypeId =5, 1, 0)) favourites_90days,
  --count(c.id) comments_90days
	from posts p
	left join votes v
        on v.postid = p.id
    left join posts a
		on a.parentid = p.id
    left join comments c
        on c.postid = p.id
	where v.votetypeid in (2, 3)
		and datediff(d, cast(p.creationdate as date),
                        cast(v.creationdate as date)) < 91
        and datediff(d, cast(p.creationdate as date),
                          cast(a.creationdate as date)) < 91
        and datediff(d, cast(p.creationdate as date),
                          cast(c.creationdate as date)) < 91
		and a.posttypeid = 2
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
                          and p.id = 38695455
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
	
-- votes/favourites
	
select p.tags, cast(p.creationdate as date) date,
  sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_days,
  sum(iif(v.VoteTypeId =5, 1, 0)) favourites_days
	from posts p
	left join votes v
        on v.postid = p.id
	where v.votetypeid in (2, 3, 5)
		and datediff(d, cast(p.creationdate as date),
                        cast(v.creationdate as date)) < 91
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
                          and p.id = 7271939
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
	
-- answers

select p.tags, cast(p.creationdate as date) date,
  count(a.id) answers_days
	from posts p
    left join posts a
		on a.parentid = p.id
        where datediff(d, cast(p.creationdate as date),
                          cast(a.creationdate as date)) < 91
		and a.posttypeid = 2
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
                          and p.id = 7271939
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
	
-- commments

select p.tags, cast(p.creationdate as date) date,
  count(c.id) comments_days
  from posts p
    left join comments c
        on c.postid = p.id
		where datediff(d, cast(p.creationdate as date),
                          cast(c.creationdate as date)) < 91
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
                          and p.id = 7271939
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
	
-- all to 90 days part 1

with v as (
	select p.tags, cast(p.creationdate as date) date,
  sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_days,
  sum(iif(v.VoteTypeId =5, 1, 0)) favourites_days
	from posts p
	left join votes v
        on v.postid = p.id
	where v.votetypeid in (2, 3, 5)
		and datediff(d, cast(p.creationdate as date),
                        cast(v.creationdate as date)) < 91
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
),
a as (
	select p.tags, cast(p.creationdate as date) date,
  count(a.id) answers_days
	from posts p
    left join posts a
		on a.parentid = p.id
        where datediff(d, cast(p.creationdate as date),
                          cast(a.creationdate as date)) < 91
		and a.posttypeid = 2
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
),
c as (
	select p.tags, cast(p.creationdate as date) date,
  count(c.id) comments_days
  from posts p
    left join comments c
        on c.postid = p.id
		where datediff(d, cast(p.creationdate as date),
                          cast(c.creationdate as date)) < 91
		and  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
)
SELECT
    cast(p.creationdate as date) post_date,
    p.tags,
    v.score_days,
	v.favourites_days,
	a.answers_days,
	c.comments_days,
    count(1) usage_cnt
FROM posts p
	left join v
		on p.tags = v.tags and cast(p.creationdate as date) = v.date
	left join a
		on p.tags = a.tags and cast(p.creationdate as date) = a.date
	left join c
		on p.tags = c.tags and cast(p.creationdate as date) = c.date
WHERE  p.tags in ('<r>', '<python>', '<java>', '<scala>', '<ruby>', '<c>',
            '<c++>', '<c#>', '<apache-spark>', '<hadoop>', '<sql>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(p.creationdate as date),
    p.tags,
	v.score_days,
	v.favourites_days,
	a.answers_days,
	c.comments_days
	
-- all to 90 days part 2

with v as (
	select p.tags, cast(p.creationdate as date) date,
  sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_days,
  sum(iif(v.VoteTypeId =5, 1, 0)) favourites_days
	from posts p
	left join votes v
        on v.postid = p.id
	where v.votetypeid in (2, 3, 5)
		and datediff(d, cast(p.creationdate as date),
                        cast(v.creationdate as date)) < 91
		and  p.tags in ('<css>', '<html>',
			'<javascript>', '<php>', '<jquery>', '<go>', '<swift>', '<vba>',
             '<shell>', '<delphi>', '<cobol>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
),
a as (
	select p.tags, cast(p.creationdate as date) date,
  count(a.id) answers_days
	from posts p
    left join posts a
		on a.parentid = p.id
        where datediff(d, cast(p.creationdate as date),
                          cast(a.creationdate as date)) < 91
		and a.posttypeid = 2
		and  p.tags in ('<css>', '<html>',
			'<javascript>', '<php>', '<jquery>', '<go>', '<swift>', '<vba>',
             '<shell>', '<delphi>', '<cobol>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
),
c as (
	select p.tags, cast(p.creationdate as date) date,
  count(c.id) comments_days
  from posts p
    left join comments c
        on c.postid = p.id
		where datediff(d, cast(p.creationdate as date),
                          cast(c.creationdate as date)) < 91
		and  p.tags in ('<css>', '<html>',
			'<javascript>', '<php>', '<jquery>', '<go>', '<swift>', '<vba>',
             '<shell>', '<delphi>', '<cobol>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
)
SELECT
    cast(p.creationdate as date) post_date,
    p.tags,
    v.score_days,
	v.favourites_days,
	a.answers_days,
	c.comments_days,
    count(1) usage_cnt
FROM posts p
	left join v
		on p.tags = v.tags and cast(p.creationdate as date) = v.date
	left join a
		on p.tags = a.tags and cast(p.creationdate as date) = a.date
	left join c
		on p.tags = c.tags and cast(p.creationdate as date) = c.date
WHERE  p.tags in ('<css>', '<html>',
			'<javascript>', '<php>', '<jquery>', '<go>', '<swift>', '<vba>',
             '<shell>', '<delphi>', '<cobol>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(p.creationdate as date),
    p.tags,
	v.score_days,
	v.favourites_days,
	a.answers_days,
	c.comments_days
	
-- all to 90 days part 3

with v as (
	select p.tags, cast(p.creationdate as date) date,
  sum(iif(v.VoteTypeId =2, 1, iif(v.VoteTypeId =3, -1, 0))) score_days,
  sum(iif(v.VoteTypeId =5, 1, 0)) favourites_days
	from posts p
	left join votes v
        on v.postid = p.id
	where v.votetypeid in (2, 3, 5)
		and datediff(d, cast(p.creationdate as date),
                        cast(v.creationdate as date)) < 91
		and  p.tags in('<pascal>', '<fortran>', '<perl>', '<rust>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
),
a as (
	select p.tags, cast(p.creationdate as date) date,
  count(a.id) answers_days
	from posts p
    left join posts a
		on a.parentid = p.id
        where datediff(d, cast(p.creationdate as date),
                          cast(a.creationdate as date)) < 91
		and a.posttypeid = 2
		and  p.tags in ('<pascal>', '<fortran>', '<perl>', '<rust>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
),
c as (
	select p.tags, cast(p.creationdate as date) date,
  count(c.id) comments_days
  from posts p
    left join comments c
        on c.postid = p.id
		where datediff(d, cast(p.creationdate as date),
                          cast(c.creationdate as date)) < 91
		and  p.tags in ('<pascal>', '<fortran>', '<perl>', '<rust>')
        and cast(p.creationdate as date) between '2006-01-01' and '2017-12-31'
        and p.posttypeid = 1
    group by p.tags, cast(p.creationdate as date)
)
SELECT
    cast(p.creationdate as date) post_date,
    p.tags,
    v.score_days,
	v.favourites_days,
	a.answers_days,
	c.comments_days,
    count(1) usage_cnt
FROM posts p
	left join v
		on p.tags = v.tags and cast(p.creationdate as date) = v.date
	left join a
		on p.tags = a.tags and cast(p.creationdate as date) = a.date
	left join c
		on p.tags = c.tags and cast(p.creationdate as date) = c.date
WHERE  p.tags in ('<pascal>', '<fortran>', '<perl>', '<rust>')
			and cast(creationdate as date)
              between '2006-01-01' and '2017-12-31'
            and posttypeid = 1
group by cast(p.creationdate as date),
    p.tags,
	v.score_days,
	v.favourites_days,
	a.answers_days,
	c.comments_days