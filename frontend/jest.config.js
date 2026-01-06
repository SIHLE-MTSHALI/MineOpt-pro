/**
 * Jest Configuration for Frontend Tests
 */

module.exports = {
    testEnvironment: 'jsdom',

    roots: ['<rootDir>/src'],

    testMatch: [
        '**/__tests__/**/*.{js,jsx}',
        '**/*.{spec,test}.{js,jsx}'
    ],

    moduleNameMapper: {
        '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
        '\\.(gif|ttf|eot|svg|png)$': '<rootDir>/src/__mocks__/fileMock.js'
    },

    setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],

    collectCoverageFrom: [
        'src/**/*.{js,jsx}',
        '!src/index.js',
        '!src/reportWebVitals.js',
        '!src/**/*.d.ts'
    ],

    coverageThreshold: {
        global: {
            branches: 70,
            functions: 70,
            lines: 70,
            statements: 70
        }
    },

    transform: {
        '^.+\\.(js|jsx)$': 'babel-jest'
    },

    moduleDirectories: ['node_modules', 'src'],

    verbose: true
};
