from checker import Checker
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector
from utils import Action


class CheckerCollectorGauge(Collector):
    def __init__(self, checkers: list[Checker], teams: int) -> None:
        super().__init__()
        self.checkers: list[Checker] = checkers
        self.teams: int = teams

    def collect(self):
        status_check_metrics_labels = [
            # "team_shortname",
            "team_id",
            "service_id",
            "service_shortname",
            "action",
        ]
        exitCode = GaugeMetricFamily(
            "ccitad_scoreboard_status_checker",
            "Scoreboard status checks",
            labels=status_check_metrics_labels,
        )

        for team in range(self.teams):
            for service in self.checkers:
                tick_info = service.get_last_tick_team_info(team)
                exitCode.add_metric(
                    [str(team), str(service.service_number), service.name, Action.CHECK_SLA.name],
                    tick_info["SLA"].value,
                )
                exitCode.add_metric(
                    [str(team), str(service.service_number), service.name, Action.GET_FLAG.name], tick_info["GET"].value
                )
                exitCode.add_metric(
                    [str(team), str(service.service_number), service.name, Action.PUT_FLAG.name], tick_info["PUT"].value
                )

        yield exitCode
