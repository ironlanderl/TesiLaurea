# POST /postFlagId
Requires a json with:
- token: auth token?
- serviceId: Checker name (like `ExCCel-1`)
- teamId: the team id
- round: round number as int
- flagId: info on how to find the flag

Return 200 when ok, anything else for error, with the reason in the response

# GET /flagIds
Optional args:
- service: Name of the checker responsible for the flag storage
- team: id of the team
- round: round number

Returns a json like this:

```json
{
  "foobar": {
    "1": {
      "5" : {
        "flag_id_description": "flag_id_service_foobar_team_1_round_5"
      }
    },
    ...
  },
  ...
}
```

# GET /
No args.

Return a json (?) with all of the services, teamIds and current round numbers
