# TODO List

- [x] Create a "configure" page in the simulations folder which can edit all of the diferent aspects of the simulation without needing to change the information in each individual page
- [ ] Create an automated debugger/test schedule  
- [x] Complete the test programs for the entire project

- [x] Integration Smoke Test: Write a lightweight test that runs RPMEESimulation.run(episodes=3) end-to-end and simply asserts that it completes without errors and produces the expected number of log entries. This will catch any interface mismatches between subsystems.
- [ ] Edge-Case Scenarios: Test how the system behaves when no sensory events are generated for several steps (e.g. force generate_input() to return empty lists). Simulate very high stress or prediction errors over many steps and assert that the replay mode damping still holds. 
- [ ] Performance Benchmark: Add a benchmark test to measure the average time per step(), to guard against regressions as you tweak parameters.
- [ ] Continuous Integration & Coverage: Hook this up into a CI pipeline (GitHub Actions, etc.) and generate coverage reports so you can see which lines aren’t exercised.
