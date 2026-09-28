from .base import Agent

ARCHITECT = Agent("architect", "Design robust software architecture and execution plans.", ["architecture","planning"])
PROGRAMMER = Agent("programmer", "Implement, debug and refactor production-quality code.", ["coding","debugging"])
DESIGNER = Agent("designer", "Design usable, coherent interfaces and design systems.", ["ui","ux","design"])
VISION = Agent("vision", "Analyze images, screenshots and visual specifications.", ["vision"])
RESEARCHER = Agent("researcher", "Research evidence, compare sources and identify uncertainty.", ["research","verification"])
TESTER = Agent("tester", "Create tests, reproduce failures and verify fixes.", ["testing","verification"])

SPECIALISTS = [ARCHITECT, PROGRAMMER, DESIGNER, VISION, RESEARCHER, TESTER]
