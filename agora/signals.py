from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from ani.models import Ani
from .models import Board, Post

_UNCHANGED = object()


@receiver(pre_save, sender=Ani)
def _stash_old_series(sender, instance, **kwargs):
    if instance.pk:
        instance._old_series_id = (
            Ani.objects.filter(pk=instance.pk).values_list('series_id', flat=True).first()
        )
    else:
        instance._old_series_id = _UNCHANGED


@receiver(post_save, sender=Ani)
def sync_board_for_ani(sender, instance, created, **kwargs):
    target_board, _ = Board.objects.get_or_create(
        name=instance.series_name,
        defaults={
            'name_zh': instance.series_name_zh,
            'name_ch': instance.series_name_ch,
        },
    )

    if created:
        target_board.anis.add(instance)
        return

    old_series_id = getattr(instance, '_old_series_id', _UNCHANGED)
    if old_series_id is _UNCHANGED or old_series_id == instance.series_id:
        return

    # 系列被改變了：把這部作品從舊看板移到新看板（同系列共用一個板）
    for old_board in instance.boards.exclude(pk=target_board.pk):
        if old_board.anis.count() == 1:
            # 舊看板原本只服務這部作品 → 整個併入新看板（貼文、關注者一起搬）
            Post.objects.filter(board=old_board).update(board=target_board)
            for user in old_board.followers.all():
                user.following_boards.add(target_board)
            old_board.delete()
        else:
            # 舊看板還涵蓋其他作品 → 只把這部作品移出，貼文留在原看板
            old_board.anis.remove(instance)

    target_board.anis.add(instance)
