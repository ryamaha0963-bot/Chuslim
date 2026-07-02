async def join_and_extract_metadata(self, record: VCRecord) -> dict:
    joined = False
    notice: Optional[str] = None
    participants: List[Any] = []

    try:
        # Obtain the user's own peer
        my_peer = await self.user_client.resolve_peer('me')
        
        # Use the call's actual params (if available)
        call_params = getattr(record.call, "params", None)
        if call_params is None:
            # Fallback: use a minimal valid structure (may still fail)
            call_params = types.DataJSON(data=json.dumps({
                "ufrag": "test",
                "pwd": "test123",
                "fingerprints": [],
                "ssrc": 11111111
            }))
            notice = "No call params found – using static ICE (join may fail)."
        else:
            notice = None

        await self.user_client.invoke(
            functions.phone.JoinGroupCall(
                call=types.InputGroupCall(id=record.call.id, access_hash=record.call.access_hash),
                join_as=my_peer,          # FIX: use user's own peer
                params=call_params,       # FIX: use real call parameters
                muted=True,
                video_stopped=True,
                invite_hash=None,
            )
        )
        joined = True
        LOGGER.info("Joined active VC in %s", record.title)
        await asyncio.sleep(2)
    except UserAlreadyParticipant:
        joined = True
        LOGGER.info("Already joined in %s", record.title)
    except (ChatAdminRequired, BadRequest) as exc:
        notice = f"Join blocked: {exc}. Fetching metadata without joining."
        LOGGER.warning("Join restriction in %s: %s", record.title, exc)
    except Exception as exc:
        notice = f"Join failed: {exc}"
        LOGGER.warning("Join attempt failed: %s", exc)

    # Fetch group call info – with error isolation
    try:
        group_call = await self.user_client.invoke(
            functions.phone.GetGroupCall(
                call=types.InputGroupCall(id=record.call.id, access_hash=record.call.access_hash),
                limit=100,
            )
        )
        call_obj = group_call.call
        params_raw = getattr(call_obj, "params", None)
        params_data = getattr(params_raw, "data", "{}") if params_raw else "{}"
        try:
            parsed = json.loads(params_data)
        except json.JSONDecodeError:
            parsed = {"raw": params_data}
        participants = getattr(group_call, "participants", [])
    except Exception as exc:
        # If we can't get call info, we still have the call object's own params
        parsed = {}
        participants = []
        notice = (notice or "") + f" GetGroupCall failed: {exc}"
        LOGGER.warning("GetGroupCall failed: %s", exc)

    # Extract IPs from parsed endpoints, servers, and deep regex (unchanged)
    extracted_ips = []
    # ... (keep the existing extraction logic, it remains correct) ...

    return {
        "title": record.title,
        "call_id": record.call.id,
        "chat_id": record.chat_id,
        "params": parsed,
        "endpoint_candidates": [],  # optional
        "extracted_ips": [
            {
                "ip": x.ip,
                "port": x.port,
                "type": x.type,
                "region": x.region,
                "source": x.source
            } for x in extracted_ips
        ],
        "joined": joined,
        "notice": notice,
        "participants_count": len(participants) if participants else 0,
    }