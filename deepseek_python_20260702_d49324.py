async def _handle_attack_confirm(self, callback_query):
    if not self.ctx.pending_attack or not self.ctx.target_ip:
        await callback_query.answer("No attack pending!", show_alert=True)
        return
    await callback_query.answer("🚀 Starting attack...")
    # Use max_duration from engine, but allow override via callback data later
    duration = self.engine.max_duration  # default
    # Optionally, ask user for duration via inline input, but for now use max
    await self._start_attack(
        callback_query.message.chat.id,
        self.ctx.target_ip,
        self.ctx.target_port,
        duration
    )