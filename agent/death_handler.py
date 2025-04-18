import logging
from typing import Dict, List, Optional, Tuple

from .resilience_tracker import ResilienceTracker

logger = logging.getLogger(__name__)

class DeathHandler:
    """Handles death recovery and item retrieval."""
    
    def __init__(self, resilience_tracker: ResilienceTracker):
        self.resilience_tracker = resilience_tracker
        self.last_death_location = None
        self.death_items = []
    
    def handle_death(self, location: str, equipment: List[str], reason: str) -> Tuple[bool, str]:
        """
        Handle a death event and determine recovery strategy.
        
        Args:
            location: Where the death occurred
            equipment: List of items lost
            reason: Cause of death
            
        Returns:
            Tuple of (success, message)
        """
        self.last_death_location = location
        self.death_items = equipment
        
        # Log the death
        self.resilience_tracker.log_death(location, equipment, reason)
        
        # Check if we should avoid this location
        if self._should_avoid_location(location, reason):
            requirements = self._calculate_requirements(location, reason)
            self.resilience_tracker.add_to_avoid_list(location, reason, requirements)
            return False, f"Location added to avoid list. Requirements to retry: {requirements}"
        
        # Try to recover items
        return self._attempt_recovery()
    
    def _should_avoid_location(self, location: str, reason: str) -> bool:
        """Determine if a location should be avoided based on death history."""
        recent_deaths = self.resilience_tracker.get_recent_deaths(5)
        location_deaths = [d for d in recent_deaths if d["location"] == location]
        
        # Avoid if more than 2 deaths in same location
        if len(location_deaths) >= 2:
            return True
            
        # Avoid if death was due to being underleveled
        if "too weak" in reason.lower() or "underleveled" in reason.lower():
            return True
            
        return False
    
    def _calculate_requirements(self, location: str, reason: str) -> Dict:
        """Calculate requirements needed to retry a location."""
        requirements = {}
        
        # Add combat requirements if death was combat-related
        if "combat" in reason.lower():
            requirements["combat_level"] = 10  # Base requirement
            requirements["health"] = 30  # Minimum health
            
            # Add specific combat skill requirements based on enemy type
            if "ranged" in reason.lower():
                requirements["ranged"] = 20
            elif "magic" in reason.lower():
                requirements["magic"] = 20
            else:
                requirements["attack"] = 20
                requirements["strength"] = 20
                requirements["defence"] = 20
        
        # Add non-combat requirements
        if "agility" in reason.lower():
            requirements["agility"] = 30
        if "thieving" in reason.lower():
            requirements["thieving"] = 25
        
        return requirements
    
    def _attempt_recovery(self) -> Tuple[bool, str]:
        """Attempt to recover items after death."""
        if not self.last_death_location or not self.death_items:
            return False, "No death location or items to recover"
        
        # Check if we can return to death location
        if self._can_return_to_death_location():
            return True, "Returning to death location to recover items"
        
        # If we can't return, go to Death's Office
        return self._handle_deaths_office()
    
    def _can_return_to_death_location(self) -> bool:
        """Check if we can return to the death location."""
        # This would check:
        # 1. If we have teleports to get there
        # 2. If we have the required items to survive the trip
        # 3. If the location is still accessible
        return False  # Placeholder - implement actual logic
    
    def _handle_deaths_office(self) -> Tuple[bool, str]:
        """Handle item recovery through Death's Office."""
        # This would:
        # 1. Check if items are available for reclaim
        # 2. Calculate reclaim cost
        # 3. Get required gold if needed
        # 4. Pay for reclaim
        return True, "Recovering items through Death's Office"
    
    def get_recovery_plan(self) -> List[str]:
        """Get the plan for recovering from death."""
        plan = []
        
        if self.last_death_location:
            # Add steps to get back to death location or Death's Office
            plan.append(f"Return to {self.last_death_location}")
            
            # Add steps to recover items
            plan.append("Recover items")
            
            # Add steps to re-equip
            for item in self.death_items:
                plan.append(f"Re-equip {item}")
            
            # Add steps to return to safe area
            plan.append("Return to safe area")
        
        return plan
    
    def update_recovery_progress(self, step: str, success: bool):
        """Update progress on death recovery."""
        if success:
            logger.info(f"Successfully completed recovery step: {step}")
        else:
            logger.warning(f"Failed recovery step: {step}")
            
        # Log the outcome
        self.resilience_tracker.log_decision_outcome(
            action=f"recovery_{step}",
            success=success,
            reward=10 if success else -5,
            context={"death_location": self.last_death_location}
        ) 