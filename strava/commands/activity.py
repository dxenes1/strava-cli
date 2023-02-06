import os

import click

from strava import api, emoji
from strava.decorators import (
    output_option,
    login_required,
    format_result,
    TableFormat,
    OutputType,
)
from strava.formatters import (
    format_distance,
    format_heartrate,
    format_speed,
    format_elevation,
    humanize,
    noop_formatter,
    format_date,
    format_seconds,
    format_activity_name,
    apply_formatters,
)

from dateparser import parse
import strava.settings

_ACTIVITY_COLUMNS = ("key", "value")
_VALID_SPORT_TYPE = [
    "AlpineSki", "BackcountrySki", "Badminton", "Canoeing", 
    "Crossfit", "EBikeRide", "Elliptical", "EMountainBikeRide", "Golf", "GravelRide", 
    "Handcycle", "HighIntensityIntervalTraining", "Hike", "IceSkate", "InlineSkate", 
    "Kayaking", "Kitesurf", "MountainBikeRide", "NordicSki", "Pickleball", "Pilates", 
    "Racquetball", "Ride", "RockClimbing", "RollerSki", "Rowing", "Run", "Sail", 
    "Skateboard", "Snowboard", "Snowshoe", "Soccer", "Squash", "StairStepper", 
    "StandUpPaddling", "Surfing", "Swim", "TableTennis", "Tennis", "TrailRun", 
    "Velomobile", "VirtualRide", "VirtualRow", "VirtualRun", "Walk", 
    "WeightTraining", "Wheelchair", "Windsurf", "Workout", "Yoga"    
]

@click.command("get-activity")
@click.argument("activity_ids", required=True, nargs=-1)
@click.option("--imperial_units", "-i", is_flag=True, default=False)
@output_option()
@login_required
def get_activity(output, activity_ids, imperial_units):
    if imperial_units:
        strava.settings.IMPERIAL_UNITS = True

    for i, activity_id in enumerate(activity_ids):
        if i > 0:
            click.echo()
        result = api.get_activity(activity_id)
        _format_activity(result, output=output)

@click.command("post-activity")
@click.option("--name", "-n", required=True)
@click.option("--type", "-t", required=False, type=click.Choice(['run', 'walk', 'ride', 'swim', 'workout']), default='workout')
@click.option("--sport_type", "-s", required=True, type=click.Choice(_VALID_SPORT_TYPE))
@click.option("--start_date_local", "-d", required=True)
@click.option("--elapsed_time", "-e", required=True, type=click.INT)
@click.option("--description", "-m", required=False, default="Uploaded with cli-tool ")
@click.option("--distance", "-l", required=False, type=click.INT, default=0)
@login_required
def post_activity(name, type, sport_type, start_date_local, elapsed_time, description, distance):
    elapsed_time = 60*elapsed_time
    start_date_local = parse(start_date_local, settings={'RETURN_AS_TIMEZONE_AWARE': True}).isoformat()
    # print(name, type, sport_type, start_date_local, elapsed_time, description, distance)
    
    return api.post_activity(
        name,
        type,
        sport_type,
        start_date_local,
        elapsed_time,
        description,
        distance
    )

@format_result(
    table_columns=_ACTIVITY_COLUMNS,
    show_table_headers=False,
    table_format=TableFormat.PLAIN,
)
def _format_activity(result, output=None):
    return result if output == OutputType.JSON.value else _as_table(result)


def _as_table(activity):
    def format_name(name):
        activity_name = format_activity_name(name, activity)
        activity_description = activity.get("description")
        return (
            f"{activity_name}{os.linesep}{activity_description}"
            if activity_description is not None
            else activity_name
        )

    def format_gear(gear):
        return f'{gear.get("name")} ({format_distance(gear.get("distance", 0))})'

    def format_heartrate_with_emoji(heartrate):
        return f"{click.style(emoji.RED_HEART, fg='red')} {format_heartrate(heartrate)}"

    def format_speed_with_emoji(speed):
        return f"{click.style(emoji.RUNNING_SHOE, fg='yellow')} {format_speed(speed)}"

    def format_elevation_with_emoji(elevation):
        difference = round(elevation)
        arrow = (
            emoji.UP_ARROW
            if difference > 0
            else emoji.DOWN_ARROW
            if difference < 0
            else emoji.RIGHT_ARROW
        )
        return f"{arrow} {format_elevation(abs(elevation))}"

    def format_split(split):
        average_heartrate = (
            format_heartrate_with_emoji(split["average_heartrate"])
            if "average_heartrate" in split
            else ""
        )
        average_speed = (
            format_speed_with_emoji(split["average_speed"])
            if "average_speed" in split
            else ""
        )
        elevation_difference = (
            format_elevation_with_emoji(split["elevation_difference"])
            if "elevation_difference" in split
            else ""
        )
        return f"{average_speed} {average_heartrate} {elevation_difference}"

    def format_property(name):
        return click.style(f"{humanize(name)}:", bold=True)

    formatters = {
        "name": format_name,
        "start_date": format_date,
        "moving_time": format_seconds,
        "distance": format_distance,
        "average_speed": format_speed,
        "max_speed": format_speed,
        "average_heartrate": format_heartrate,
        "max_heartrate": format_heartrate,
        "total_elevation_gain": format_elevation,
        "calories": noop_formatter,
        "device_name": noop_formatter,
        "gear": format_gear,
    }

    basic_data = [
        {"key": format_property(k), "value": v}
        for k, v in apply_formatters(activity, formatters).items()
    ]
    split_data = [
        {
            "key": format_property(f"Split {split.get('split')}"),
            "value": format_split(split),
        }
        for split in activity.get("splits_metric", [])
    ]

    return [*basic_data, *split_data]
