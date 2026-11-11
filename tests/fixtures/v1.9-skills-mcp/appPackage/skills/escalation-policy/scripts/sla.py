def minutes_open(opened, now):
    return (now - opened).total_seconds() / 60
