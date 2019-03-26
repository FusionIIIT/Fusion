def seen_or_x(notifications, x=10):
    notifs = notifications.filter(seen=False)
    flag = notifs.count() < x
    if flag:
        notifs = notifications.order_by("-timestamp")[0:x]
    return notifs


def type_sort_notifs(notifications, seenify=True):
    all_notif_types = list()
    for dic in notifications.values("notif_type").distinct():
        for key, value in dic.items():
            all_notif_types.append(value)
    type_sorted_notifs = dict()
    for notif_type in all_notif_types:
        notifs = notifications.filter(notif_type=notif_type)
        if seenify:
            notifs = seen_or_x(notifs)
        type_sorted_notifs[notif_type] = notifs
    context = {
                "type_sorted_notifs": type_sorted_notifs,
                "all_notif_types": all_notif_types,
              }
    return context
