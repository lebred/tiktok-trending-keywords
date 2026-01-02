"""
Momentum scoring algorithm.

Implements the deterministic scoring algorithm from BUILD_SPEC.md:
- Lift: (avg(last_7) - avg(prev_21)) / (avg(prev_21) + 0.01)
- Acceleration: slope(last_7) - slope(prev_21)
- Novelty: 1 - percentile_rank(avg(prev_90))
- Noise: stdev(last_7) / (avg(last_7) + 0.01)
- Raw: 0.45*lift + 0.35*acceleration + 0.25*novelty - 0.25*noise
- Score: int(100 / (1 + exp(-raw))) clamped to [1, 100]
"""

import logging
import math
import statistics
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for calculating momentum scores."""

    # Period definitions (in weeks)
    LAST_7_WEEKS = 7
    PREV_21_WEEKS = 21
    PREV_90_WEEKS = 90

    # Score weights
    LIFT_WEIGHT = 0.45
    ACCELERATION_WEIGHT = 0.35
    NOVELTY_WEIGHT = 0.25
    NOISE_WEIGHT = -0.25

    @staticmethod
    def extract_weekly_values(trends_data: Dict[str, Any]) -> List[float]:
        """
        Extract weekly values from Google Trends data.

        Args:
            trends_data: Dictionary from GoogleTrendsService

        Returns:
            List of weekly trend values (0-100 scale), most recent first
        """
        if not trends_data or "data" not in trends_data:
            return []

        values = []
        keyword = trends_data.get("keyword", "")

        for record in trends_data["data"]:
            # Get the keyword column value
            if keyword and keyword in record:
                value = record[keyword]
            else:
                # Fallback: get first numeric column (excluding isPartial)
                value = None
                for key, val in record.items():
                    if isinstance(val, (int, float)) and key != "isPartial":
                        value = val
                        break

            if value is not None:
                values.append(float(value))

        # Reverse to get most recent first (Google Trends returns oldest first)
        return list(reversed(values))

    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """Calculate average of values."""
        if not values:
            return 0.0
        return statistics.mean(values)

    @staticmethod
    def calculate_slope(values: List[float]) -> float:
        """
        Calculate linear regression slope of values.

        Args:
            values: List of numeric values

        Returns:
            Slope (positive = increasing, negative = decreasing)
        """
        if len(values) < 2:
            return 0.0

        # Use linear regression: y = mx + b
        # x = index (0, 1, 2, ...)
        # y = value
        n = len(values)
        x = np.arange(n)
        y = np.array(values)

        # Calculate slope: m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x_squared = np.sum(x * x)

        denominator = n * sum_x_squared - sum_x * sum_x
        if abs(denominator) < 1e-10:  # Avoid division by zero
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return float(slope)

    @staticmethod
    def calculate_percentile_rank(value: float, all_values: List[float]) -> float:
        """
        Calculate percentile rank of a value within a list.

        Percentile rank = (number of values below) / (total number of values)

        Args:
            value: Value to rank
            all_values: List of all values to rank against

        Returns:
            Percentile rank (0.0 to 1.0)
        """
        if not all_values:
            return 0.5  # Default to median if no data

        sorted_values = sorted(all_values)
        count_below = sum(1 for v in sorted_values if v < value)
        count_equal = sum(1 for v in sorted_values if v == value)

        # Percentile rank: (count_below + 0.5 * count_equal) / total
        total = len(sorted_values)
        percentile_rank = (count_below + 0.5 * count_equal) / total

        return percentile_rank

    @staticmethod
    def calculate_lift(
        last_7_weeks: List[float], prev_21_weeks: List[float]
    ) -> float:
        """
        Calculate lift metric.

        lift = (avg(last_7) - avg(prev_21)) / (avg(prev_21) + 0.01)

        Args:
            last_7_weeks: Last 7 weeks of values
            prev_21_weeks: Previous 21 weeks of values

        Returns:
            Lift value
        """
        if not last_7_weeks or not prev_21_weeks:
            return 0.0

        avg_last_7 = ScoringService.calculate_average(last_7_weeks)
        avg_prev_21 = ScoringService.calculate_average(prev_21_weeks)

        denominator = avg_prev_21 + 0.01
        lift = (avg_last_7 - avg_prev_21) / denominator

        return lift

    @staticmethod
    def calculate_acceleration(
        last_7_weeks: List[float], prev_21_weeks: List[float]
    ) -> float:
        """
        Calculate acceleration metric.

        acceleration = slope(last_7) - slope(prev_21)

        Args:
            last_7_weeks: Last 7 weeks of values
            prev_21_weeks: Previous 21 weeks of values

        Returns:
            Acceleration value
        """
        if len(last_7_weeks) < 2 or len(prev_21_weeks) < 2:
            return 0.0

        slope_last_7 = ScoringService.calculate_slope(last_7_weeks)
        slope_prev_21 = ScoringService.calculate_slope(prev_21_weeks)

        acceleration = slope_last_7 - slope_prev_21

        return acceleration

    @staticmethod
    def calculate_novelty(
        prev_90_weeks: List[float], all_historical: List[float]
    ) -> float:
        """
        Calculate novelty metric.

        novelty = 1 - percentile_rank(avg(prev_90))

        Args:
            prev_90_weeks: Previous 90 weeks of values
            all_historical: All historical values for percentile ranking

        Returns:
            Novelty value (0.0 to 1.0)
        """
        if not prev_90_weeks:
            return 0.0

        avg_prev_90 = ScoringService.calculate_average(prev_90_weeks)

        # Use all historical data for percentile ranking
        if not all_historical:
            all_historical = prev_90_weeks

        percentile_rank = ScoringService.calculate_percentile_rank(
            avg_prev_90, all_historical
        )

        novelty = 1.0 - percentile_rank

        return novelty

    @staticmethod
    def calculate_noise(last_7_weeks: List[float]) -> float:
        """
        Calculate noise metric (coefficient of variation).

        noise = stdev(last_7) / (avg(last_7) + 0.01)

        Args:
            last_7_weeks: Last 7 weeks of values

        Returns:
            Noise value
        """
        if len(last_7_weeks) < 2:
            return 0.0

        avg_last_7 = ScoringService.calculate_average(last_7_weeks)
        stdev_last_7 = statistics.stdev(last_7_weeks)

        denominator = avg_last_7 + 0.01
        noise = stdev_last_7 / denominator

        return noise

    @classmethod
    def calculate_score(
        cls,
        weekly_values: List[float],
        min_weeks_required: int = 28,  # Need at least 28 weeks (7 + 21)
    ) -> Optional[Dict[str, float]]:
        """
        Calculate momentum score for a keyword.

        Args:
            weekly_values: List of weekly trend values (most recent first)
            min_weeks_required: Minimum weeks of data required

        Returns:
            Dictionary with all metrics and scores, or None if insufficient data
        """
        if len(weekly_values) < min_weeks_required:
            logger.warning(
                f"Insufficient data: {len(weekly_values)} weeks, "
                f"need at least {min_weeks_required}"
            )
            return None

        # Extract periods (most recent first)
        last_7_weeks = weekly_values[:7]
        prev_21_weeks = weekly_values[7:28]  # Weeks 7-27 (21 weeks)
        prev_90_weeks = (
            weekly_values[28:118] if len(weekly_values) >= 118 else weekly_values[28:]
        )  # Weeks 28-117 (90 weeks)

        # Calculate metrics
        lift = cls.calculate_lift(last_7_weeks, prev_21_weeks)
        acceleration = cls.calculate_acceleration(last_7_weeks, prev_21_weeks)
        novelty = cls.calculate_novelty(prev_90_weeks, weekly_values)
        noise = cls.calculate_noise(last_7_weeks)

        # Calculate raw score
        raw_score = (
            cls.LIFT_WEIGHT * lift
            + cls.ACCELERATION_WEIGHT * acceleration
            + cls.NOVELTY_WEIGHT * novelty
            + cls.NOISE_WEIGHT * noise
        )

        # Calculate final score: sigmoid function
        # score = int(100 / (1 + exp(-raw)))
        try:
            final_score = int(100 / (1 + math.exp(-raw_score)))
        except (OverflowError, ValueError):
            # Handle extreme values
            if raw_score > 10:
                final_score = 100
            elif raw_score < -10:
                final_score = 1
            else:
                final_score = 50  # Default

        # Clamp to [1, 100]
        final_score = max(1, min(100, final_score))

        return {
            "momentum_score": final_score,
            "raw_score": raw_score,
            "lift_value": lift,
            "acceleration_value": acceleration,
            "novelty_value": novelty,
            "noise_value": noise,
        }

    @classmethod
    def calculate_score_from_trends_data(
        cls, trends_data: Dict[str, Any]
    ) -> Optional[Dict[str, float]]:
        """
        Calculate score directly from Google Trends data.

        Args:
            trends_data: Dictionary from GoogleTrendsService

        Returns:
            Dictionary with all metrics and scores, or None if insufficient data
        """
        weekly_values = cls.extract_weekly_values(trends_data)
        return cls.calculate_score(weekly_values)

