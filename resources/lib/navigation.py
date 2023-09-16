import logging
import os
import routing

from resources.lib.tmdbv3api.objs.discover import Discover
from resources.lib.tmdbv3api.objs.search import Search
from resources.lib.tmdbv3api.objs.trending import Trending
from resources.lib.tmdbv3api.objs.genre import Genre
from resources.lib.tmdbv3api.tmdb import TMDb
from resources.lib.tmdb import (
    TMDB_POSTER_URL,
    add_icon_genre,
    tmdb_show_results,
)
from resources.lib.anilist import search_anilist
from resources.lib.utils import (
    api_show_results,
    clear,
    filter_by_episode,
    filter_by_quality,
    get_fanartv,
    history,
    play,
    search_api,
    sort_results,
)
from resources.lib.kodi import (
    ADDON_PATH,
    addon_settings,
    get_setting,
    hide_busy_dialog,
    notify,
)
from resources.lib.tmdbv3api.objs.season import Season
from resources.lib.tmdbv3api.objs.tv import TV

from xbmcgui import ListItem
from xbmc import Keyboard
from xbmcplugin import addDirectoryItem, endOfDirectory, setPluginCategory


plugin = routing.Plugin()


@plugin.route("/")
def main_menu():
    setPluginCategory(plugin.handle, "Main Menu")
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search_tmdb, mode="multi", genre_id=-1, page=1),
        list_item("Search", "search.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search_tmdb, mode="tv", genre_id=-1, page=1),
        list_item("TV Shows", "tv.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search_tmdb, mode="movie", genre_id=-1, page=1),
        list_item("Movies", "movies.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(anime_menu),
        list_item("Anime", "movies.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(genre_menu),
        list_item("By Genre", "movies.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(direct_menu),
        list_item("Direct Search", "search.png"),
        isFolder=True,
    )

    addDirectoryItem(
        plugin.handle,
        plugin.url_for(settings),
        list_item("Settings", "settings.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(main_history),
        list_item("History", "history.png"),
        isFolder=True,
    )
    endOfDirectory(plugin.handle)


@plugin.route("/direct")
def direct_menu():
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search, mode="multi", query=None, id=None, tracker="all"),
        list_item("Search", "search.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search, mode="tv", query=None, id=None, tracker="all"),
        list_item("TV Search", "tv.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search, mode="movie", query=None, id=None, tracker="all"),
        list_item("Movie Search", "movies.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search, mode="multi", query=None, id=None, tracker="anime"),
        list_item("Anime Search", "search.png"),
        isFolder=True,
    )
    endOfDirectory(plugin.handle)


@plugin.route("/anime")
def anime_menu():
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(anilist, category="search"),
        list_item("Search", "search.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(
            anilist,
            category="Popular",
        ),
        list_item("Popular", "tv.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(anilist, category="Trending"),
        list_item("Trending", "movies.png"),
        isFolder=True,
    )
    endOfDirectory(plugin.handle)


@plugin.route("/genre")
def genre_menu():
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search_tmdb, mode="tv_genres", genre_id=-1, page=1),
        list_item("TV Shows", "tv.png"),
        isFolder=True,
    )
    addDirectoryItem(
        plugin.handle,
        plugin.url_for(search_tmdb, mode="movie_genres", genre_id=-1, page=1),
        list_item("Movies", "movies.png"),
        isFolder=True,
    )
    endOfDirectory(plugin.handle)


@plugin.route("/search/<mode>/<query>/<id>/<tracker>")
def search(mode, query, id, tracker):
    results = search_api(query, mode, tracker)
    if results:
        f_quality = filter_by_quality(results)
        sorted_res = sort_results(f_quality)
        api_show_results(sorted_res, plugin, id, mode="movies", func=play_torrent)


@plugin.route(
    "/search_season/<query>/<tvdb_id>/<episode_name>/<episode_num>/<season_num>/<tracker>"
)
def search_tv_episode(query, tvdb_id, episode_name, episode_num, season_num, tracker):
    results = search_api(query=query, mode="tv", tracker=tracker)
    if results:
        f_episodes = filter_by_episode(results, episode_name, episode_num, season_num)
        f_quality = filter_by_quality(f_episodes, mode="tv_episode")
        sorted_res = sort_results(f_quality)
        api_show_results(sorted_res, plugin, tvdb_id, mode="tv", func=play_torrent)


@plugin.route("/play_torrent")
def play_torrent():
    url, magnet, title = plugin.args["query"][0].split(" ", 2)
    play(url=url, title=title, magnet=magnet)


@plugin.route("/search_tmdb/<mode>/<genre_id>/<page>")
def search_tmdb(mode, genre_id, page):
    page = int(page)
    genre_id = int(genre_id)

    tmdb = TMDb()
    api_key = get_setting("tmdb_apikey", "b70756b7083d9ee60f849d82d94a0d80")
    tmdb.api_key = api_key

    if mode == "multi":
        keyboard = Keyboard("", "Search on TMDB:", False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            text = keyboard.getText().strip()
        else:
            hide_busy_dialog()
            return
        search_ = Search()
        results = search_.multi(str(text), page=page)
        tmdb_show_results(
            results,
            func=search,
            next_func=next_page,
            page=page,
            plugin=plugin,
            mode=mode,
        )
    elif mode == "movie":
        if genre_id != -1:
            discover = Discover()
            movies = discover.discover_movies({"with_genres": genre_id, "page": page})
            tmdb_show_results(
                movies.results,
                func=search,
                next_func=next_page,
                page=page,
                plugin=plugin,
                genre_id=genre_id,
                mode=mode,
            )
        else:
            trending = Trending()
            movies = trending.movie_week(page=page)
            tmdb_show_results(
                movies.results,
                func=search,
                next_func=next_page,
                page=page,
                plugin=plugin,
                genre_id=genre_id,
                mode=mode,
            )
    elif mode == "tv":
        if genre_id != -1:
            discover = Discover()
            tv_shows = discover.discover_tv_shows(
                {"with_genres": genre_id, "page": page}
            )
            tmdb_show_results(
                tv_shows.results,
                func=tv_details,
                next_func=next_page,
                page=page,
                plugin=plugin,
                genre_id=genre_id,
                mode=mode,
            )
        else:
            trending = Trending()
            shows = trending.tv_day(page=page)
            tmdb_show_results(
                shows.results,
                func=tv_details,
                next_func=next_page,
                page=page,
                plugin=plugin,
                genre_id=genre_id,
                mode=mode,
            )
    elif mode == "movie_genres":
        menu_genre(mode, page)
    elif mode == "tv_genres":
        menu_genre(mode, page)


@plugin.route("/tv/details/<id>")
def tv_details(id):
    tv = TV()
    details = tv.details(id)

    show_name = details.name
    number_of_seasons = details.number_of_seasons
    tvdb_id = details.external_ids.tvdb_id

    fanart_data = get_fanartv(tvdb_id)
    if fanart_data:
        poster = fanart_data["clearlogo2"]
        fanart = fanart_data["fanart2"]
    else:
        poster = (
            TMDB_POSTER_URL + details.poster_path if details.get("poster_path") else ""
        )
        fanart = poster

    for i in range(number_of_seasons):
        number = i + 1
        title = f"Season {number}"

        list_item = ListItem(label=title)
        list_item.setArt(
            {
                "poster": poster,
                "fanart": fanart,
                "icon": os.path.join(ADDON_PATH, "resources", "img", "trending.png"),
            }
        )
        list_item.setInfo(
            "video",
            {"title": title, "mediatype": "video", "plot": f"{details.overview}"},
        )
        list_item.setProperty("IsPlayable", "false")

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                tv_season_details,
                show_name=show_name,
                id=id,
                tvdb_id=tvdb_id,
                season_num=number,
            ),
            list_item,
            isFolder=True,
        )

    endOfDirectory(plugin.handle)


@plugin.route("/tv/details/season/<show_name>/<id>/<tvdb_id>/<season_num>")
def tv_season_details(show_name, id, tvdb_id, season_num):
    season = Season()
    tv_season = season.details(id, season_num)

    for ep in tv_season.episodes:
        episode_name = ep.name
        episode_num = f"{ep.episode_number:02}"
        season_num_ = f"{int(season_num):02}"

        title = f"{season_num}x{episode_num}. {episode_name}"
        air_date = ep.air_date
        duration = ep.runtime

        poster = TMDB_POSTER_URL + ep.still_path if ep.get("still_path") else ""

        list_item = ListItem(label=title)
        list_item.setArt(
            {
                "poster": poster,
                "icon": os.path.join(ADDON_PATH, "resources", "img", "trending.png"),
            }
        )
        list_item.setInfo(
            "video",
            {
                "title": title,
                "mediatype": "video",
                "aired": air_date,
                "duration": duration,
                "plot": f"{ep.overview}",
            },
        )
        list_item.setProperty("IsPlayable", "false")

        addDirectoryItem(
            plugin.handle,
            plugin.url_for(
                search_tv_episode,
                show_name,
                tvdb_id,
                episode_name,
                episode_num,
                season_num_,
                "all",
            ),
            list_item,
            isFolder=True,
        )

    endOfDirectory(plugin.handle)


@plugin.route("/anilist/<category>")
def anilist(category, page=1):
    search_anilist(category, page, plugin, action=search, next_action=next_page_anilist)


@plugin.route("/next_page/anilist/<category>/<page>")
def next_page_anilist(category, page):
    search_anilist(
        category, int(page), plugin, action=search, next_action=next_page_anilist
    )


@plugin.route("/next_page/<mode>/<page>/<genre_id>")
def next_page(mode, page, genre_id):
    search_tmdb(mode=mode, genre_id=int(genre_id), page=int(page))


@plugin.route("/settings")
def settings():
    addon_settings()


@plugin.route("/history")
def main_history():
    history(plugin, clear_history, play_torrent)


@plugin.route("/history/clear")
def clear_history():
    clear()


def list_item(label, icon):
    item = ListItem(label)
    item.setArt(
        {
            "icon": os.path.join(ADDON_PATH, "resources", "img", icon),
            "thumb": os.path.join(ADDON_PATH, "resources", "img", icon),
        }
    )
    return item


def menu_genre(mode, page):
    if mode == "movie_genres":
        movies = Genre().movie_list()
        for gen in movies.genres:
            if gen["name"] == "TV Movie":
                continue
            name = gen["name"]
            item = ListItem(label=name)
            add_icon_genre(item, name)
            addDirectoryItem(
                plugin.handle,
                plugin.url_for(
                    search_tmdb, mode="movie", genre_id=gen["id"], page=page
                ),
                item,
                isFolder=True,
            )
    elif mode == "tv_genres":
        tv = Genre().tv_list()
        for gen in tv.genres:
            name = gen["name"]
            item = ListItem(label=name)
            add_icon_genre(item, name)
            addDirectoryItem(
                plugin.handle,
                plugin.url_for(search_tmdb, mode="tv", genre_id=gen["id"], page=page),
                item,
                isFolder=True,
            )
    endOfDirectory(plugin.handle)


def run():
    try:
        plugin.run()
    except Exception as e:
        logging.error("Caught exception:", exc_info=True)
        notify(str(e))