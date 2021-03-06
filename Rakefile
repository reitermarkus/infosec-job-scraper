# frozen_string_literal: true

require 'logger'
require 'date'
require 'pathname'
require 'json'
require 'digest'
require 'set'
require 'selenium-webdriver'

DATA_DIR = Pathname(__dir__).join('data')

# Helper functions for `ENV`.
module EnvExtension
  def headless?
    !self['HEADLESS'].nil?
  end
end

# Module for making functions available globally.
module Kernel
  def log
    @log ||= Logger.new(STDOUT)
  end
end

ENV.extend(EnvExtension)

# WebDriver wrapper, allowing for connection reset.
class Driver < Delegator
  def initialize
    __setobj__ begin
      driver = if (remote_url = ENV['REMOTE_WEBDRIVER_URL'])
        Selenium::WebDriver.for(:remote, url: remote_url, desired_capabilities: :firefox)
      else
        options = Selenium::WebDriver::Firefox::Options.new(args: [*(ENV.headless? ? '--headless' : nil)])
        Selenium::WebDriver.for(:firefox, options: options)
      end
      driver.manage.timeouts.implicit_wait = 5
      driver.manage.window.size = Selenium::WebDriver::Dimension.new(1280, 1024)
      driver
    end
  end

  def __getobj__
    @driver
  end

  def __setobj__(obj)
    @driver = obj
  end

  def reset(duration = nil)
    quit rescue nil
    sleep duration if duration
    initialize
  end
end

def driver
  @driver ||= Driver.new
end

def with_retry(*exceptions)
  tries ||= 0
  yield
rescue *exceptions => e
  log.error "#{e.class}: #{e}"
  driver.reset 2**tries

  tries += 1
  log.error "Would raise: #{e}" if tries > 3
  # raise if tries > 3

  log.error "Retrying (#{tries}) …"
  retry
end

def get_jobs(mod)
  driver.extend(mod)

  log.info "Looking for jobs on #{mod.name} …"
  jobs = with_retry Selenium::WebDriver::Error::NoSuchWindowError, Selenium::WebDriver::Error::UnknownError do
    driver.search('information security')
  end
  log.info "Found #{jobs.count} jobs on #{mod.name}."

  jobs.each do |url|
    file = DATA_DIR.join("#{mod.name.downcase}-#{Digest::SHA2.hexdigest(url)}.json")

    if file.exist?
      log.info "#{file.basename} already exists."
      next
    end

    log.info "Fetching “#{url}” …"

    details = with_retry Selenium::WebDriver::Error::NoSuchWindowError, Selenium::WebDriver::Error::UnknownError do
      driver.get_detail_page(url)
    end

    next if details.nil?

    details[:url] = url
    details[:date] = Date.today.iso8601

    file.dirname.mkpath
    file.write JSON.pretty_generate(details)

    log.info "Saved #{file.basename}."
  end
end

task default: :scrape

task scrape: %i[indeed stepstone monster]

task :deduplicate do
  paths = Pathname.glob(DATA_DIR.join('*.json'))

  duplicates = paths.map { |path| [path, JSON.parse(File.read(path))] }
                    .sort_by { |_, json| json['date'] }
                    .group_by { |_, json| [json['title'], json['content']] }
                    .values
                    .select { |v| v.count > 1 }

  duplicates.each do |ds|
    *delete, keep = ds.map(&:first)

    delete.each do |path|
      log.info "Deleting '#{path}'."
      path.delete
    end

    log.info "Keeping '#{keep}'."
  end
end

# https://simplemaps.com/data/at-cities
file 'nlp/cities.json' do |task|
  path = task.name
  sh 'curl', '-sL', 'https://simplemaps.com/static/data/country-cities/at/at.json', '-o', path
  cities = JSON.parse(File.read(path))
  File.write path, JSON.pretty_generate(cities.map { |city| [city['city'], city['admin']] }.to_h)
end

task :python_venv do
  ENV['VIRTUAL_ENV'] = "#{__dir__}/nlp/venv"
  ENV['PATH'] = "#{ENV['VIRTUAL_ENV']}/bin:#{ENV['PATH']}"

  sh 'python3', '-m', 'venv', ENV['VIRTUAL_ENV']
  sh 'python3', '-m', 'pip', 'install', '-r', 'nlp/requirements.txt'
end

task nlp: [:python_venv, 'nlp/cities.json'] do
  sh 'python3', 'nlp/detect.py'
end

task jupyter: :python_venv do
  exec 'jupyter', 'notebook', '.'
end

task graphs: :python_venv do
  sh 'jupyter', 'nbconvert', '--to', 'notebook', '--ClearOutputPreprocessor.enabled=True',
     '--execute', 'nlp/graphs.ipynb', '--inplace'
end

task :tex do
  cd 'tex'
  sh 'latexmk', '-cd'
end
