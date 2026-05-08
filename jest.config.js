export default {
  testEnvironment: 'jsdom',
  testMatch: ['**/*.test.js'],
  collectCoverageFrom: [
    'web/components/**/*.js',
    '!web/components/**/*.test.js'
  ],
  coverageDirectory: 'coverage',
  verbose: true,
  transform: {},
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1'
  }
};
