from datetime import datetime
from datetime import timedelta
from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from app.api.dependencies.db_connection import get_db
from app.core.config import TEMPLATE_DIR

router = APIRouter(prefix="/report")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


@router.get("/questions")
def questions(request: Request, db: Session = Depends(get_db)):
    """
    Question 1: Who are the 10 most active users?
    """
    sql = text('SELECT user_id,"user".name FROM playlist LEFT JOIN "user" ON user_id="user".id GROUP BY user_id, "user".name ORDER BY SUM(listened_at) LIMIT 10')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for Question 1: {result}")

    q1_users = [{"user_id":row[0], "user_name":row[1]} for row in result]

    """
    Question 2: How many users were active on the 1st of March 2019?
    """
    start = int(datetime.strptime("01.03.2019 00:00:01", "%d.%m.%Y %H:%M:%S").timestamp())  # 1551394801
    end = int(datetime.strptime("01.03.2019 23:59:59", "%d.%m.%Y %H:%M:%S").timestamp())  # 1551481199
    sql = text(f'SELECT DISTINCT COUNT(DISTINCT user_id) FROM playlist WHERE listened_at BETWEEN {start} AND {end}')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for Question 2: {result}")
    q2_users = result[0][0]

    """
    Question 3: For every user, what was the first song they listened to?
    """
    sql = text(
        'SELECT DISTINCT ON (user_id) user_id, "user".name AS user_name, track_id, track.name AS track_name FROM playlist LEFT JOIN "user" ON playlist.user_id = "user".id LEFT JOIN track ON track.msid = playlist.track_id GROUP BY user_id, "user".name, track_id, track.name ORDER BY user_id, MIN(listened_at)')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for Question 3: {result}")
    q3_songs = [row for row in result]

    """
    Question 4: What two songs are most often played directly after one another?
    """
    sql = text(
        'SELECT track_id, next, count(*) FROM (SELECT user_id, track_id, lead(track_id) over (order by user_id) as next FROM playlist GROUP BY user_id,track_id) as tuples GROUP BY track_id, next HAVING count(*) > 1 ORDER BY count desc LIMIT 10')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for Question 4: {result}")
    q4_songs = [{"first_track":row[0], "second_track": row[1], "times_played":row[2]} for row in result]

    """
    Question 5: How many users are only listening to songs from Bob Dylan?
    """

    sql = text(
        "SELECT count(*) FROM (SELECT user_id, array_agg(track_id) as track_ids FROM playlist GROUP BY user_id) as tracks WHERE tracks.track_ids <@ ARRAY(SELECT DISTINCT msid FROM track WHERE artist_id = (SELECT msid FROM artist WHERE name LIKE 'Bob Dylan'))")
    result = db.execute(sql).fetchall()
    logger.info(f"Result for Question 5: {result}")
    q5_users = result[0][0]

    result_dict = {"q1": q1_users, "q2": q2_users, "q3": q3_songs, "q4": q4_songs, "q5": q5_users}

    return templates.TemplateResponse('questions_template.html',
                                      context={"request": request, "status": "success", "result": result_dict})

    # return {"status": "success", "result": result_dict}


@router.get("/kpis")
def kpis(request: Request, db: Session = Depends(get_db)):
    kpi_question = "<div> <h3>The CEO asks you to provide them with a management report containing the most important metrics that you can distill from the dataset. " \
                   "</br> The desired output is a table showing how these metrics develop over time. </br> " \
                   "</br> Consider what the most important metrics are and generate the report using sql queries or a python script. </h3> </div>"

    # Metrics:
    a_reasoning = "<div> <h4> Reasoning: </h4> </br> " \
                  "To see how many users there are, how many of them are daily active users and what are the general activity patterns </br>" \
                  "on the platform. This helps to extract improvements on the platform and also scale the infrastructure to the demands </br>" \
                  "for example when there are heavy load hours throughout a day. Also it helps to find out the ratio active users and </br>" \
                  "in what timespan vs overall userbase and analyzing on how to increase that number. </div>"

    # A: Amount of Users
    sql = text('SELECT count(*) FROM "user"')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for amount of users: {result}")
    amount_users = result[0][0]

    # A.1: Overall played tracks:
    sql = text('SELECT COUNT(*) FROM playlist')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for amount of tracks played: {result}")
    tracks_played = result[0][0]

    # A.2: Most active users:
    sql = text('SELECT user_id,"user".name, COUNT(user_id) FROM playlist LEFT JOIN "user" ON playlist.user_id = "user".id GROUP BY user_id, "user".name ORDER BY COUNT(user_id) DESC LIMIT 10')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for most active users: {result}")
    most_active_users = [{"user_id":row[0], "user_name":row[1], "count":row[2]} for row in result]

    # A.3: Daily active users:
    query_text = 'SELECT "Date", COUNT("Date") FROM (SELECT DISTINCT user_id, date_trunc(' + "'day', to_timestamp(listened_at)) AS " + '"Date" FROM playlist GROUP BY listened_at, user_id ORDER BY "Date") as dates GROUP BY "Date"'
    sql = text(query_text)
    result = db.execute(sql).fetchall()
    logger.info(f"Result for daily active users: {result}")
    daily_active_user = [{"date":str(datetime.strptime(str(row[0])[:10], "%Y-%m-%d").date()),"count":row[1]} for row in result]

    # A.4: Mean activity frequency of users:
    query_text = "SELECT DISTINCT user_id, date_trunc('day', to_timestamp(listened_at)) AS " + '"Date" FROM playlist GROUP BY user_id, listened_at ORDER BY user_id'
    sql = text(query_text)
    result = db.execute(sql).fetchall()
    #logger.info(f"Result for mean activity frequency of users: {result}")

    # subtracting datetimes gives timedeltas

    from collections import defaultdict
    d = defaultdict(list)

    for k, *v in result:
        d[k].append(v)

    timedeltas_by_user = {}
    for i in range(1,len(d.keys())):
        timedeltas = []
        for j in range(1, len(d[i]) - 1):
            timedeltas.append(d[i][j-1][0] - d[i][j][0])
        timedeltas_by_user[i] = timedeltas
    #logger.info(timedeltas_by_user.items())
    average_timedelta_by_user = {}
    for key, value in timedeltas_by_user.items():
        if value:
            average_timedelta_by_user[key] = sum(value, timedelta(0)) / len(value)
            average_timedelta_by_user[key] = int(average_timedelta_by_user[key].seconds/3600)




    mean_activity_user = [{"user_id":key, "mean":value} for key,value in average_timedelta_by_user.items()]

    logger.info(mean_activity_user)

    # A.5: Most active hours of the day
    query_text = 'SELECT extract(hour FROM dates."Date") as hours, COUNT(*) FROM (SELECT DISTINCT user_id, date_trunc(' + "'hour', to_timestamp(listened_at)) AS " + '"Date" FROM playlist GROUP BY user_id, listened_at ORDER BY user_id) as dates GROUP BY hours ORDER BY hours'
    sql = text(query_text)
    result = db.execute(sql).fetchall()
    logger.info(f"Result for most active hours of the day: {result}")
    most_active_hours = [{"hour":int(row[0]), "activity":row[1]} for row in result]

    b_reasoning = "<div> <h4> Reasoning: </h4> </br> " \
                  "To see the distribution of artists and tracks on the platform. what tracks are the most liked, what artists are the </br>" \
                  "most liked. What artists have the most tracks and what percentage of the platform they are taking. Helps to maybe </br>" \
                  "diversify the offering of the platform and also maybe do special collaborations or exclusives with the artists. </br>" \
                  "Also encouraging less represented artists that have more tracks to publish them also. </div>"

    # B: Amount of Tracks and Artists
    sql = text('SELECT count(*) FROM "track"')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for amount of tracks: {result}")
    amount_tracks = result[0][0]

    sql = text('SELECT count(*) FROM "artist"')
    result = db.execute(sql).fetchall()
    logger.info(f"Result for amount of artists: {result}")
    amount_artists = result[0][0]

    # B.1: Most listened to tracks
    sql = text(
        "SELECT joined.name ,COUNT(*) FROM (SELECT * FROM playlist LEFT JOIN track ON playlist.track_id = track.msid ORDER BY track_id ) joined GROUP BY  joined.name ORDER BY count desc LIMIT 10")
    result = db.execute(sql).fetchall()
    logger.info(f"Result for most listened to tracks: {result}")
    most_listened_to_tracks = [{"song":row[0], "count":row[1]} for row in result]

    # B.2: Most listened to artists:
    sql = text(
        "SELECT joined.artist_name, count(*) FROM (SELECT * FROM playlist LEFT JOIN (SELECT track.msid AS track_msid, artist.msid AS artist_msid, artist.name AS artist_name FROM artist LEFT JOIN track ON track.artist_id = artist.msid) as at ON playlist.track_id = at.track_msid ORDER BY at.artist_msid) as joined GROUP BY joined.artist_name ORDER BY count desc LIMIT 10")
    result = db.execute(sql).fetchall()
    logger.info(f"Result for most listened to artists: {result}")
    most_listened_to_artists = [{"artist_name":row[0], "count":row[1]} for row in result]

    # B.3: Artists with the most tracks
    sql = text(
        "SELECT artist_name, count(*) FROM (SELECT track.msid AS track_msid, artist.msid AS artist_msid, artist.name AS artist_name FROM artist LEFT JOIN track ON track.artist_id = artist.msid ORDER BY artist_msid) as joined GROUP BY artist_name ORDER BY count DESC LIMIT 10 ")
    result = db.execute(sql).fetchall()
    logger.info(f"Result for artists with most tracks: {result}")
    most_represented_artists = [{"artist_name":row[0], "count":row[1]} for row in result]

    other_metrics = "<div> <h3>What other metrics (that aren't available in the given dataset) would you like to add to the report? " \
                    "</br> Prioritize your top 3. </br> " \
                    "Shortly describe your reasoning for what metrics you picked and why you decided to include them in the report.</h3> </div>" \
                    "Metrics I would have also included: </br>" \
                    "1. Genre of the Tracks and Artists </br>" \
                    "Reasoning: </br>" \
                    "Finding out what Genres are the most popular, What is the overal offering of the platform etc. </br>" \
                    "2. More info about the user like age distribution or gender and location </br>" \
                    "Reasoning: </br>" \
                    "General information about the userbase, trend forecasting what age group/userbase will like what songs/genre in future what is trending at the moment etc. </br>" \
                    "3. Percentage of the Song listened to / Skipped a certain part </br>" \
                    "Reasoning: </br>" \
                    "Are there parts of songs that are especially popular and others that are not. Can we find songs with similar patterns to recommend to the users </br>" \
                    "</div>"

    result_dict = {
        "kpi_question": kpi_question,
        "a_reasoning": a_reasoning,
        "amount_users": amount_users,
        "tracks_played": tracks_played,
        "most_active_users": most_active_users,
        "daily_active_user": daily_active_user,
        "mean_activity_user": mean_activity_user,
        "most_active_hours": most_active_hours,
        "b_reasoning": b_reasoning,
        "amount_tracks": amount_tracks,
        "amount_artists": amount_artists,
        "most_listened_to_tracks": most_listened_to_tracks,
        "most_listened_to_artists": most_listened_to_artists,
        "most_represented_artists": most_represented_artists,
        "other_metrics": other_metrics
    }
    return templates.TemplateResponse('kpi_template.html',
                                      context={"request": request, "status": "success", "result": result_dict})
    # return {"status": "success", "results": result_dict}
