from bot.domain.drawdown_state import DrawdownState
from bot.domain.ports import DrawdownRepository, NotifierPort, UserConfigRepository


class HandleDrawdown:
    def __init__(
        self,
        drawdown_repo: DrawdownRepository,
        user_config_repo: UserConfigRepository,
        notifier: NotifierPort,
    ):
        self._drawdown_repo = drawdown_repo
        self._user_config_repo = user_config_repo
        self._notifier = notifier

    async def execute(self, user_id: int, pnl_usdt: float) -> DrawdownState | None:
        config = await self._user_config_repo.get(user_id)
        if config is None:
            return None

        state = await self._drawdown_repo.get(user_id)
        if state is None:
            state = DrawdownState(user_id=user_id)

        state.apply_pnl(pnl_usdt, config.capital_total)

        if state.should_pause(config.max_drawdown_percent):
            state.is_paused = True
            await self._notifier.send_warning(
                config.chat_id,
                f"🚨 SISTEMA PAUSADO\n\n"
                f"Drawdown máximo alcanzado: {abs(state.current_drawdown_percent):.1f}%\n"
                f"({abs(state.current_drawdown_usdt):.2f} USDT)\n\n"
                f"Las señales están suspendidas.\n"
                f"Usa /resume cuando estés listo para continuar.",
            )
        elif state.should_warn(config.max_drawdown_percent):
            await self._notifier.send_warning(
                config.chat_id,
                f"⚠️ Drawdown Warning\n\n"
                f"Tu drawdown actual es de {state.current_drawdown_percent:.1f}%\n"
                f"({abs(state.current_drawdown_usdt):.2f} USDT)\n\n"
                f"Has alcanzado el 50% del límite máximo ({config.max_drawdown_percent}%).\n"
                f"Revisa tu gestión de riesgo.",
            )

        await self._drawdown_repo.save(state)
        return state

    async def reset(self, user_id: int) -> DrawdownState:
        return await self._drawdown_repo.reset(user_id)

    async def resume(self, user_id: int) -> None:
        state = await self._drawdown_repo.get(user_id)
        if state is None:
            state = DrawdownState(user_id=user_id)
        state.is_paused = False
        await self._drawdown_repo.save(state)
